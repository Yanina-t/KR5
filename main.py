import json

import requests

from utils import DBManager, create_database, save_data_to_database
from config import config


# Список компаний
from utils import DBManager
companies_list = ['Lamoda tech', 'Альфа-Банк', 'TINKOFF', 'VK', 'X5 Tech', 'Совкомбанк ПАО ', 'Лига Цифровой Экономики',
                  'I Like IT', 'amoCRM', 'ООО ЛингуаЛео', 'Skyeng']
#
# companies_list = ['X5 Tech']
list_company_vacancy = DBManager().get_companies_and_vacancies_count(companies_list)
# print(list_company_vacancy)
# for i in list_company_vacancy:
#     print(f"Компания - {i['company']}, количество открытых вакансий - {i['open_vacancies']}")
# #
list_vacancy = DBManager().get_all_vacancies(list_company_vacancy)
# print(list_vacancy)
# # for i in list_vacancy:
#     if i['salary'] == 0:
#         i['salary'] = 'не указано'
#     print(f"Компания - {i['company']}, вакансия - {i['vacancy']}, оплата - {i['salary']}, ссылка на вакансию - {i['url_vacancy']}")

def main():
    params = config()
    create_database('hh', params)
    save_data_to_database(list_company_vacancy, list_vacancy, 'hh', params)

if __name__ == '__main__':
    main()


# date = [{'company': list_company_vacancy}, {'vacancy': list_vacancy}]
# save_data_to_database(date)
# print(date)

# list_company_vacancy = []
# for company in companies_list:
#     payload = {
#         'text': company,
#         'only_with_vacancies': True,
#         'per_page': 100,
#     }
#     url = 'https://api.hh.ru/employers'
#     request = requests.get(url, payload)
#     js_data = request.json()
#     list_company_vacancy.append({
#         'company': js_data['items'][0]['name'],
#         'id_company': js_data['items'][0]['id'],
#         'open_vacancies': js_data['items'][0]['open_vacancies'],
#     })
#     print(js_data)
# print(list_company_vacancy)
