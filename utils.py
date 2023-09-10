import requests
import psycopg2
from numpy.core.defchararray import lower


def create_database(database_name: str, params: dict) -> None:
    """Создание базы данных и таблиц для сохранения данных о компаниях и вакансиях."""

    conn = psycopg2.connect(dbname=database_name, **params)
    conn.autocommit = True
    cur = conn.cursor()

    # cur.execute(f"DROP DATABASE {database_name}")  # удалить БД
    cur.execute(f"CREATE DATABASE {database_name}")  # создать БД

    conn.close()

    conn = psycopg2.connect(dbname=database_name, **params)

    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE companies (
                id_company INTEGER PRIMARY KEY,
                company VARCHAR(255) NOT NULL,
                open_vacancies INTEGER,
                vacancies_url TEXT
                )
            """)

    with conn.cursor() as cur:
        cur.execute("""
                CREATE TABLE vacancies (
                    id_company INT REFERENCES company(id_company) ,
                    company VARCHAR(100) NOT NULL,
                    id_vacancy SERIAL PRIMARY KEY,
                    vacancy VARCHAR(100) NOT NULL,
                    salary INT NOT NULL,
                    url_vacancy TEXT
                )
            """)

    conn.commit()
    conn.close()


def get_companies(companies: list):
    """Получение данных о компаниях"""
    list_company_vacancy = []
    for company in companies:
        payload = {
            'text': company,
            'only_with_vacancies': True,
            'per_page': 50,
        }
        url = 'https://api.hh.ru/employers'
        request = requests.get(url, payload)
        js_data = request.json()
        list_company_vacancy.append({
            'company': js_data['items'][0]['name'],
            'id_company': js_data['items'][0]['id'],
            'open_vacancies': js_data['items'][0]['open_vacancies'],
            'url_vacancies': js_data['items'][0]['vacancies_url']
        })
    return list_company_vacancy


def get_vacancies(list_company_vacancy: list):
    """Получение данных о вакансиях """
    # как вывести более 20 вакансии? Как сделать пагинацию?
    list_vacancy_salary = []
    page = 0
    payload = {
        'page': page,
        'per_page': 50,
    }
    for i in list_company_vacancy:
        url = i['url_vacancies']
        request = requests.get(url, payload)
        js_company_vacancy = request.json()
        for vacancy in js_company_vacancy['items']:
            vacancy_and_salary = {
                'company': vacancy['employer']['name'],
                'id_company': vacancy['employer']['id'],
                'vacancy': vacancy['name'],
                'id_vacancy': vacancy['id'],
                'url_vacancy': vacancy['alternate_url'],
            }
            if vacancy['salary'] is not None:
                vacancy_and_salary['salary'] = 0 if vacancy.get('salary').get('from') is None else vacancy.get(
                    'salary').get('from')
            else:
                vacancy_and_salary['salary'] = 0
            list_vacancy_salary.append(vacancy_and_salary)
            page += 1
    return list_vacancy_salary


def save_data_to_database(list_company: list[dict[str, any]], list_vacancy: list[dict[str, any]],
                          database_name: str, params: dict):
    """Сохранение данных о компаниях и вакансиях, в базу данных."""

    conn = psycopg2.connect(dbname=database_name, **params)

    with conn.cursor() as cur:
        for company_vac in list_company:
            cur.execute(
                """
            INSERT INTO companies (id_company, company, open_vacancies, url_vacancies)
            VALUES (%s, %s, %s, %s)
            RETURNING id_company
            """,
                (company_vac['id_company'], company_vac['company'],
                 company_vac['open_vacancies'], company_vac['vacancies_url'])
            )
        for vacancy_l in list_vacancy:
            cur.execute(
                """
                INSERT INTO vacancies (id_company, company, id_vacancy, vacancy, salary, url_vacancy)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id_company
                """,
                (vacancy_l['id_company'], vacancy_l['company'], vacancy_l['id_vacancy'], vacancy_l['vacancy'],
                 vacancy_l['salary'], vacancy_l['url_vacancy'])
            )


class DBManager:
    """Создайте класс DBManager, который будет подключаться к БД PostgreSQL и иметь следующие методы:"""

    def __init__(self, database_name: str, params: dict):
        self.conn = psycopg2.connect(dbname=database_name, **params)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

    def get_companies_and_vacancies_count(self):
        """Получает список всех компаний и количество вакансий у каждой компании."""
        query = """
                SELECT companies.company, COUNT(vacancies.id_company) AS vacancy_count
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
            SELECT id_vacancy, vacancy, salary FROM vacancy
            WHERE vacancy LIKE '%{text1}%' or vacancy LIKE '%{text2}%'
            """
        )
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()
