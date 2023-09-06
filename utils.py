import psycopg2
import requests

def create_database(database_name: str, params: dict) -> None:
    """Создание базы данных и таблиц для сохранения данных о компаниях и вакансиях."""

    conn = psycopg2.connect(dbname='postgres', **params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE {database_name}") #удалить БД
    cur.execute(f"CREATE DATABASE {database_name}") #создать БД

    conn.close()

    conn = psycopg2.connect(dbname=database_name, **params)

    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE company (
                id_company INTEGER PRIMARY KEY,
                company VARCHAR(255) NOT NULL,
                open_vacancies INTEGER,
                url_vacancies TEXT
                )
            """)

    with conn.cursor() as cur:
        cur.execute("""
                CREATE TABLE vacancy (
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


def save_data_to_database(list_company_vacancy: list[dict[str, any]], list_vacancy: list[dict[str, any]], database_name: str, params: dict):
    """Сохранение данных о каналах и видео в базу данных."""

    conn = psycopg2.connect(dbname=database_name, **params)

    with conn.cursor() as cur:
        for company_vac in list_company_vacancy:
            cur.execute(
            """
            INSERT INTO company (id_company, company, open_vacancies, url_vacancies)
            VALUES (%s, %s, %s, %s)
            RETURNING id_company
            """,
            (company_vac['id_company'], company_vac['company'],
            company_vac['open_vacancies'], company_vac['url_vacancies'])
        )
        for vacancy_l in list_vacancy:
            cur.execute(
                """
                INSERT INTO vacancy (id_company, company, id_vacancy, vacancy, salary, url_vacancy)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id_company
                """,
                (vacancy_l['id_company'], vacancy_l['company'], vacancy_l['id_vacancy'], vacancy_l['vacancy'],
                 vacancy_l['salary'], vacancy_l['url_vacancy'])
            )
            # id_company = cur.fetchone()[0]
            # videos_data = channel['videos']
            # for video in videos_data:
            #     video_data = video['snippet']
            #     cur.execute(
            #         """
            #         INSERT INTO videos (channel_id, title, publish_date, video_url)
            #         VALUES (%s, %s, %s, %s)
            #         """,
            #         (channel_id, video_data['title'], video_data['publishedAt'],
            #          f"https://www.youtube.com/watch?v={video['id']['videoId']}")
            #     )
    conn.commit()
    conn.close()


class DBManager:
    """Создайте класс DBManager, который будет подключаться к БД PostgreSQL и иметь следующие методы:"""

    def get_companies_and_vacancies_count(self, companies: list):
        """Получает список всех компаний и количество вакансий у каждой компании."""
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

    def get_all_vacancies(self, list_company_vacancy: list):
        """Получает список всех вакансий с указанием названия компании, названия вакансии и зарплаты и ссылки на
        вакансию."""
        # как вывести более 20 вакансии? Как сделать пагинацию?
        list_vacancy_salary = []
        for i in list_company_vacancy:
            url = i['url_vacancies']
            print(url)
            request = requests.get(url)
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
        return list_vacancy_salary

    def get_avg_salary(self, list_vacancy_salary: list):
        """Получает среднюю зарплату по вакансиям."""

    pass

    def get_vacancies_with_higher_salary(self):
        """Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям."""

    pass

    def get_vacancies_with_keyword(self):
        """Получает список всех вакансий, в названии которых содержатся переданные в метод слова, например python."""

    pass
