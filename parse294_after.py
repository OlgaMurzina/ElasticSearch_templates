# задача: построить связь между "idStatusLong" и "qqc" по индексу 294* со скроллом помощью конструкта after из запроса _search

import datetime as dt
import json
import configparser
from requests.auth import HTTPBasicAuth
import requests

# данные для запроса из локальной системы
start_time = dt.datetime.now()
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')
LOGIN = config.get('ES', 'LOGIN')[1:-1]
PASS = config.get('ES', 'PASS')[1:-1]
BASIC = HTTPBasicAuth(LOGIN, PASS)
HOST = config.get('ES', 'HOST')[1:-1]
PORT = '9200'
HEADER = {'Content-Type': 'application/json'}
INDEX_NAME = config.get('ES', 'INDEX_NAME')[1:-1]
URL = f'{HOST}:{PORT}/{INDEX_NAME}/_search'
# размер выгружаемой порции данных
D = 10000
# вспомогательный запрос на общее кол-во документов в индексе
URL_ALL = f'{HOST}:{PORT}/{INDEX_NAME}/_count'
search_body = ''
all_size = requests.get(URL_ALL, auth=BASIC, data=search_body, headers=HEADER).json()["count"]
print(f"all_size={all_size}")
# тело для первого запроса к индексу
search_body = json.dumps({"size": D,
                          "_source": [
                              "idStatusLong", "qqc"
                          ],
                          "sort": [
                              {
                                  "idStatusLong": {
                                      "order": "asc"
                                  }
                              }
                          ]})
response = requests.get(URL, auth=BASIC, data=search_body, headers=HEADER).json()
scroll_size = len(response['hits']['hits'])
# номер последней записи из первой кучи
after_num = response['hits']['hits'][-1]['sort']
print(after_num)
# парсинг скроллом
IdStatusLong_qqc = {}
ctrl_search = scroll_size
while (scroll_size > 0):
    for status in response["hits"]["hits"]:
        if status["_source"]["idStatusLong"] in IdStatusLong_qqc.keys():
            IdStatusLong_qqc[status["_source"]["idStatusLong"]].append(status["_source"]["qqc"])
        else:
            IdStatusLong_qqc[status["_source"]["idStatusLong"]] = [status["_source"]["qqc"]]
    print(f'len_statuses={len(IdStatusLong_qqc.keys())}, ctrl={ctrl_search}')
    search_body = json.dumps({"size": D,
                              "_source": [
                                  "idStatusLong", "qqc"
                              ],
                              "search_after": after_num,
                              "sort": [
                                  {
                                      "idStatusLong": {
                                          "order": "asc"
                                      }
                                  }
                              ]})
    if after_num:
        response = requests.get(URL, auth=BASIC, data=search_body, headers=HEADER).json()
    else:
        break
    if response['hits']['hits'][-1]['sort']:
        after_num = response['hits']['hits'][-1]['sort']
    else:
        after_num = 0
    scroll_size = len(response['hits']['hits'])
    ctrl_search += scroll_size

# вывод первых 100 значений из словаря для контроля
for key in list(IdStatusLong_qqc.keys())[:100]:
    print(f'{key}: {IdStatusLong_qqc[key]}')
# выгрузка словаря в json файл
with open(f'IdStatusLong_qqc_after{dt.datetime.now()}.json', 'w') as outfile:
    json.dump(IdStatusLong_qqc, outfile)
finish_time = dt.datetime.now()
# индикатор для лога, что процесс прошел штатно
if ctrl_search == all_size:
    print('OK')
else:
    print(f'Не совпадают размеры выгрузки и индекса: all_size={all_size}, ctrl={ctrl_search}')
print(f'Время выгрузки: {finish_time - start_time}')
