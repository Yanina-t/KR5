import time
import requests
import psycopg2
from numpy.core.defchararray import lower


def create_database(database_name: str, params: dict) -> None:
    """Создание базы данных и таблиц для сохранения данных о компаниях и вакансиях."""

    conn = psycopg2.connect(dbname='postgres', **params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE IF EXISTS {database_name}")  # удалить БД
    cur.execute(f"CREATE DATABASE {database_name}")  # создать БД

    conn.close()

    conn = psycopg2.connect(dbname=database_name, **params)

    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE companies (
                id_company INTEGER PRIMARY KEY,
                company VARCHAR(255) NOT NULL,
                open_vacancies INTEGER,
                url_vacancies TEXT
                )
            """)

    with conn.cursor() as cur:
        cur.execute("""
                CREATE TABLE vacancies (
                    id_company INT REFERENCES companies(id_company),
                    id_vacancy SERIAL PRIMARY KEY,
                    company VARCHAR(100) NOT NULL,
                    id_vacancy_in_company TEXT, 
                    vacancy VARCHAR(100) NOT NULL,
                    salary INT NOT NULL,
                    url_vacancy TEXT
                )
            """)

    conn.commit()
    conn.close()


def get_companies(company: str):
    """Получение данных о компаниях"""
    payload = {
        'text': company,
        'only_with_vacancies': True,
        'per_page': 50,
    }
    url = 'https://api.hh.ru/employers'
    request = requests.get(url, payload)
    js_data = request.json()
    return {
        'company': js_data['items'][0]['name'],
        'id_company': js_data['items'][0]['id'],
        'open_vacancies': js_data['items'][0]['open_vacancies'],
        'url_vacancies': js_data['items'][0]['vacancies_url']
    }


def get_vacancies(company_vacancies: str):
    """Получение данных о вакансиях """
    # как вывести более 20 вакансии? Как сделать пагинацию?
    list_vacancy_salary = []
    response = requests.get(company_vacancies)
    js_company_vacancy = response.json()
    pages = js_company_vacancy['pages']
    while True:
        for page in range(pages):

            response = requests.get(company_vacancies, params={'page': page + 1})

            vacancies = response.json()

            if vacancies.get('items', None) is None or len(vacancies['items']) == 0:
                continue
            else:
                vacancies_items = vacancies['items']
                for vacancy in vacancies_items:
                    vacancy_and_salary = {
                        'company': vacancy['employer']['name'],
                        'id_company': vacancy['employer']['id'],
                        'vacancy': vacancy['name'],
                        'id_vacancy': vacancy['id'],
                        'url_vacancy': vacancy['alternate_url'],
                        'salary': vacancy['salary']['from'] if vacancy.get('salary') else 0
                    }
                    if vacancy['salary'] is not None:
                        vacancy_and_salary['salary'] = 0 if vacancy['salary'].get('from') is None else vacancy[
                            'salary'].get('from')
                    else:
                        vacancy_and_salary['salary'] = 0
                    list_vacancy_salary.append(vacancy_and_salary)
            time.sleep(10)
        break
    return list_vacancy_salary


def save_data_to_database(company: dict[str, str], list_vacancy: list[dict[str, any]],
                          database_name: str, params: dict):
    """Сохранение данных о компаниях и вакансиях, в базу данных."""

    conn = psycopg2.connect(dbname=database_name, **params)

    with conn.cursor() as cur:
        query = "INSERT INTO companies (id_company, company, open_vacancies, url_vacancies) VALUES (%s, %s, %s, %s)"
        cur.execute(query, (company['id_company'], company['company'], company['open_vacancies'],
                            company['url_vacancies']))
        for vacancy_l in list_vacancy:
            query = ("INSERT INTO vacancies (id_company, company, id_vacancy_in_company, vacancy, salary, url_vacancy) "
                     "VALUES (%s, %s, %s, %s, %s, %s)")
            cur.execute(query, (
                vacancy_l['id_company'], vacancy_l['company'], vacancy_l['id_vacancy'], vacancy_l['vacancy'],
                vacancy_l['salary'], vacancy_l['url_vacancy']))
        conn.commit()


class DBManager:
    """Создайте класс DBManager, который будет подключаться к БД PostgreSQL и иметь следующие методы:"""

    def __init__(self, database_name: str, params: dict):
        self.conn = psycopg2.connect(dbname=database_name, **params)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

    def get_companies_and_vacancies_count(self):
        """Получает список всех компаний и количество вакансий у каждой компании."""
        query = """
                SELECT companies.company, COUNT(vacancies.id_vacancy) AS vacancy_count
                FROM companies
                LEFT JOIN vacancies ON companies.id_company = vacancies.id_company
                GROUP BY companies.company
                """
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_all_vacancies(self):
        """Получает список всех вакансий с указанием названия компании, названия вакансии и зарплаты и ссылки на
        вакансию."""
        query = """
                SELECT companies.company, vacancies.vacancy, vacancies.salary, vacancies.url_vacancy
                FROM companies
                JOIN vacancies ON companies.id_company = vacancies.id_company
                """
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_avg_salary(self):
        """Получает среднюю зарплату по вакансиям."""
        query = "SELECT ROUND(AVG(salary) ,2) FROM vacancies;"
        self.cur.execute(query)
        return self.cur.fetchone()[0]

    def get_vacancies_with_higher_salary(self):
        """Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям."""
        query = """
            SELECT id_vacancy, vacancy, salary FROM vacancies
            WHERE salary > (SELECT ROUND(AVG(salary) ,2) FROM vacancy)
            ORDER by salary
            """
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_vacancies_with_keyword(self, text):
        """Получает список всех вакансий, в названии которых содержатся переданные в метод слова, например python."""
        text1 = text.title()
        text2 = lower(text)
        self.cur.execute(
            f"""
            SELECT id_vacancy, vacancy, salary FROM vacancies
            WHERE vacancy LIKE '%{text1}%' or vacancy LIKE '%{text2}%'
            """
        )
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()
