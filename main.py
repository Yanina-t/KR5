from config import config
from utils import create_database, get_companies, get_vacancies, save_data_to_database, DBManager

companies_list = ['Lamoda tech', 'Альфа-Банк', 'TINKOFF', 'VK', 'X5 Tech', 'Совкомбанк ПАО ', 'Лига Цифровой Экономики',
                  'I Like IT', 'amoCRM', 'ООО ЛингуаЛео', 'Skyeng']


def main():
    # params = config()
    # database_name = 'hh'
    # create_database(database_name, params)  # создание БД и таблиц
    # list_company = get_companies(companies_list)  # получение данных о компаниях
    # list_vacancy = get_vacancies(list_company)  # получение данных о вакансиях
    # save_data_to_database(list_company, list_vacancy, database_name, params)  # сохранение данных в БД

    params = config()
    database_name = 'hh'
    create_database(database_name, params)  # создание БД и таблиц
    for company in companies_list:
        company_info = get_companies(company)
        list_vacancy = get_vacancies(company_info['url_vacancies'])
        save_data_to_database(company_info, list_vacancy, database_name, params)

    db_manager = DBManager(database_name, params)
    print(db_manager.get_companies_and_vacancies_count())
    print(db_manager.get_all_vacancies())
    print(db_manager.get_avg_salary())

    keyword = input("Введите ключевое слово для поиска вакансий: ")
    vacancies = db_manager.get_vacancies_with_keyword(keyword)
    if vacancies:
        print(f"Вакансии, содержащие ключевое слово '{keyword}':")
        for vacancy in vacancies:
            print(vacancy)
    else:
        print(f"Вакансии с ключевым словом '{keyword}' не найдены.")

    db_manager.close()


if __name__ == "__main__":
    main()
