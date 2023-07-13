# задача: построить связь между "idStatusLong" и "qqc" по индексу 294* со скроллом из scrollAPI ElasticSearch

import configparser
import datetime as dt
import json
from requests.auth import HTTPBasicAuth
from elasticsearch import Elasticsearch, helpers, exceptions

# данные для запроса из локальной системы
start_time = dt.datetime.now()
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')
LOGIN = config.get('ES', 'LOGIN')[1:-1]
PASS = config.get('ES', 'PASS')[1:-1]
BASIC = HTTPBasicAuth(LOGIN, PASS)
HOST = config.get('ES', 'HOST')[1:-1]
PORT = "9200"
URL = f'{HOST}:{PORT}'
INDEX_NAME = config.get('ES', 'INDEX_NAME')[1:-1]
# размер выгружаемой порции данных
D = 10000

client = Elasticsearch(URL, http_auth=(LOGIN, PASS))
# проверка наличия подключения клиента к ES
try:
    # получение информации от клиента
    client_info = Elasticsearch.info(client)
    print('Elasticsearch client info:', json.dumps(client_info, indent=4))
except exceptions.ConnectionError as err:
    print('Elasticsearch client error:', err)
    client = None
# ----------
# выгрузка с логикой scrollAPI
# ----------
if client != None:
    search_body = {"size": D,
                   "_source": [
                       "idStatusLong", "qqc"
                   ],
                   "sort": [
                       {
                           "idStatusLong": {
                               "order": "asc"
                           }
                       }
                   ]}
    response = client.search(
        index=INDEX_NAME,
        body=search_body,
        scroll='2m',  # время выплнения поискового запроса
    )
    # get the number of docs with len()
    print("total docs:", len(response["hits"]["hits"]))
    # фиксация первого _scrollID
    scroll_id = response["_scroll_id"]
    # контроль - сколько всего записей на источнике
    all_size = response['hits']['total']['value']
    print(f'all_size={all_size}')
    # контроль размера батча
    scroll_size = len(response['hits']['hits'])
    ctrl_search = scroll_size
    # словарь связи между "idStatusLong" и "qqc"
    IdStatusLong_qqc = {}
    while (scroll_size > 0):
        for status in response["hits"]["hits"]:
            if status["_source"]["idStatusLong"] in IdStatusLong_qqc.keys():
                IdStatusLong_qqc[status["_source"]["idStatusLong"]].append(status["_source"]["qqc"])
            else:
                IdStatusLong_qqc[status["_source"]["idStatusLong"]] = [status["_source"]["qqc"]]
        print(f'len_statuses={len(IdStatusLong_qqc.keys())}, ctrl={ctrl_search}')
        response = client.scroll(
            scroll_id=scroll_id,
            scroll='10s',  # time value for search
        )
        scroll_id = response['_scroll_id']
        scroll_size = len(response['hits']['hits'])
        ctrl_search += scroll_size
# вывод первых 100 значений из словаря для контроля
for key in list(IdStatusLong_qqc.keys())[:100]:
    print(f'{key}: {IdStatusLong_qqc[key]}')
# выгрузка словаря в json файл
with open(f'IdStatusLong_qqc_scroll{dt.datetime.now()}.json', 'w') as outfile:
    json.dump(IdStatusLong_qqc, outfile)
finish_time = dt.datetime.now()
# индикатор для лога, что процесс прошел штатно
if ctrl_search == all_size:
    print('OK')
else:
    print(f'Не совпадают размеры выгрузки и индекса: all_size={all_size}, ctrl={ctrl_search}')
print(f'Время выгрузки: {finish_time - start_time}')
