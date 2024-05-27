# ElasticSearch_templates  (*for me*)

##  Эксперименты со scroll
Создала два файла с разными методами scroll по данным ES.
Решала одну и ту же задачу:  
- формирование словаря зависимых инициализаторов, где родитель является начальной подстрокой потомка. Полученный словарь записывала в файл для дальнейшего преиспользования без выгрузки данных (предполагаю возможность дописывания в него обновлений - следующая задача).

##  ScrollAPI  
Для реализации этого метода можно воспользоваться мастером подключений из состава ElasticSearch или использовать изменение заголовка запроса добавлением для второго и последующих запросов параметра _search_id="value".
- В файле parse_294_scroll_api.py выполнена реализация с подключением через мастера. 
Получила разночтения при установленном локально ElasticSearch 8.8 запрос к удаленной ElasticSearch 7.3 выдавал ошибку. Пришлось снести локальную ES 8.8 и установить ES 7.10. Все заработало без каких-либо проблем.  
**Вывод:**  
- зависит от версии, что не является хорошо, т.к. может вызвать проблемы в будущем при работе с локальной и удаленной разноверсионными ES.
- очень медленно отрабатывает - в три раза медленнее, чем after.  
![результат scrollAPI](https://github.com/OlgaMurzina/ElasticSearch_templates/blob/main/scrollAPIresult.png)  
- Возможно, дело в работе клиента ES, попробую еще реализацию через requests. Есть надежда, что будет быстрее работать.

## After 
Для реализации скролла с использованием параметра after при той же логике заметила, что выгрузка работает быстрее. Замеры по времени опубликую.
Реализация простая, через requests - обязательна сортировка по выбранному полю. Именно к нему и привязывается параметр after.
В первом запросе все, как обычно, а начиная со второго запроса в тело включается часть логики, связанная с after:  
![тело запроса](https://github.com/OlgaMurzina/ElasticSearch_templates/blob/main/scroll_after_two_request.png)  
Тут важно аккуратно выгружать этот параметр из пришедшего запроса! Пока я не решила проблему с хвостом - последний батч не выгрузился и не попал в обработку.
Ищу ошибку - почему появилась разница в кол-ве выгруженных документов и имеющихся в индексе. Удалось чуть-чуть уменьшить недостачу изменением направления сортировки, но она не исчезла и составляет примерно 1700 записей.
![ошибка](https://github.com/OlgaMurzina/ElasticSearch_templates/blob/main/after_bag.png)

Самые частые запросы к эластику:
Ольга Мурзина, [07.11.2023 13:10]
# просмотр кол-ва документов на индексе
GET /153/_count
{
  "query": {
    "bool": {
      "filter": [
        {
          "bool": {
            "must": [
              {
                "nested": {
                  "path": "X",
                    "query": {
                      "bool": {
                        "must": [
                          {
                            "range": {
                              "X.datetime": {
                                "gte": "19700101 00:00:00",
                                "lte": "20201226 00:00:00"                          }
                            }
                          }]
                      }
                    }
                  }
                }
            ]
          }
        }
      ]
    }
  }
}


# кол-во записей в общей витрине
GET /services_showcase_1/_count

# 1 уровень полноты данных
GET /services_showcase_1/_search
{ "size": 200,
  "query": {
    "bool": {
      "must_not": [
        {"exists": {
          "field": "idEpisodLong"
          }
        }
      ],
      "must": [
        {"exists": {
          "field": "idPatient"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "idPatient"}
    }
  }
}

# 2 уровень полноты данных
GET /services_showcase_1/_search
{ "size": 200, 
  "query": {
    "bool": {
      "must_not": [
        {"exists": {
          "field": "idServiceLong"
          }
        }
      ],
      "must": [
        {"exists": {
          "field": "idEpisodLong"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "idEpisodLong"}
    }
  }
}

# 3 уровень полноты данных
GET /services_showcase_1/_search
{ "size": 200, 
  "query": {
    "bool": {
      "must_not": [
        {"exists": {
          "field": "idStatusLong"
          }
        }
      ],
      "must": [
        {"exists": {
          "field": "idServiceLong"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "idServiceLong"}
    }
  }
}

# 4 уровень полноты данных
GET /services_showcase_1/_search
{"size": 200, 
  "query": {
    "bool": {
      
      "must": [
        {"exists": {
          "field": "idStatusLong"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "idStatusLong"}
    }
  }
}

# проверка наличия/отсутствия _id = idPatient/idEpisodLong/idServiceLong
GET /services_showcase_1/_search
{"size": 50, 
  "query": {
    "match_phrase": {
      "_id": "dABAAОнACL"
    }
  }
}

# проверка уникальности idPatient при записях 1 уровня полноты данных
GET /services_showcase_1/_search
{"size": 50, 
  "query": {
    "match_phrase": {
      "idPatient": "yAGAeЦ["
    }
  }, 
  "sort": [
    {
      "_id": {
        "order": "desc"
      }
    }
  ]
}

# проверка уникальности idEpisodLong при 2 уровне полноты данных
GET /services_showcase_1/_search
{"size": 50, 
  "query": {
    "match_phrase": {
      "idEpisodLong": "yAGAfZ9AAF"
    }
  }, 
  "sort": [
    {
      "_id": {
        "order": "desc"
      }
    }
  ]
}

# проверка уникальности idServiceLong при 3 уровне полноты данных
GET /services_showcase_1/_search
{"size": 50,
  "query": {
    "match_phrase": {
      "idServiceLong": "dABAAтЦABiAAA11:29A"
    }
  }, 
  "sort": [
    {
      "_id": {
        "order": "desc"
      }
    }
  ]
}

Ольга Мурзина, [07.11.2023 13:10]
# агрегирующий запрос к витрине по списку ключей на примере idPatient
GET services_showcase_1/_search
{
   "size": 0,
   "query": {
      "bool": {
         "must": {
            "terms": {
               "idPatient": ["yAGBAS;", "uBKAATP", "uBKAAJ8", "dABAAF]", "uBKAAHr"]
            }
         }
      }
   },
   "aggs": {
      "aggregation_name_1": {
         "terms": {
            "size": 10000,
            "field": "idPatient"
         },
         "aggs": {
            "aggregation_name_2": {
               "top_hits": {
                  "size": 1,
                  "_source": ["idPatient", "pJ", "pI", "X.datetime", "sn", "pB", "fio", "partOfdata"]
               }
            }
         }
      }
   }
}

# Запрос к витрине на агрегацию по типу операций
# SQL
GET /_sql?format=txt
{
  "query": 
  """SELECT tn type,
            count(idServiceLong) cnt
     FROM services_showcase_1 
     WHERE ((pDatop between 20180101 and 20200901) and 
           (panv is not  null) and 
           (pANdop like '%выполнено%') and 
           (tn like '%Операция%'))
    GROUP BY tn
    ORDER BY cnt DESC"""
}

GET /153/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "exists": {
            "field":"n566"
          }
        }
      ]
    }
  },
  "aggs": {
    "cnt": {
      "value_count": {
        "field": "idPatient"
      }
    }
  }
}

GET /153/_search
{"query": {
    "bool": {
        "must": [
            
            {
            "exists": {"field": "n566"}
            }
        ]
    }
},
  "aggs": {
    "n566": {
      "terms": {
        "field": "n566",
        "size": 10
      }
    }
  }
}

GET /244/_count
 {
  "query": {
      "bool": {
        "filter": [
          {
          "bool": {
              "must": [
                {"exists": {"field": "pID"}},
                  {
                  "nested": {
                      "path": "X",
                      "query": {
                          "bool": {
                              "must": [
                                  {
                                  "range": {
                                      "X.datetime": {
                                          "gte": "20210101 00:00:00",
                                          "lte": "20220101 00:00:00"
                                    }
                                  }
                                }
                              ]
                            }
                      }
                  }
                  }
                ]
            }
          }
        ]
      }
    }
 }


GET /293/_search
{"_source": ["idPatient", "idEpisodLong", "idServiceLong"], 
  "query": {
    "bool": {
        "must_not": [
            
            {
            "exists": {"field": "idStatusLong"}
            }
        ]
    }
},
"aggs": {
  "cnt": {
    "value_count": {
      "field": "idStatusLong"
    }
  }
}
}

GET /293/_count
{}

Ольга Мурзина, [07.11.2023 13:11]
######################
# data-preproccesing #
######################

GET /data-preproccesing/_search
{"query": {"match": {"_id": "test_showcase_1"}}}

#######
# 153 #
#######

# просмотр кол-ва документов на индексе
GET /153/_count
{
  "query": {
    "bool": {
      "filter": [
        {
          "bool": {
            "must": [
              {
                "nested": {
                  "path": "X",
                    "query": {
                      "bool": {
                        "must": [
                          {
                            "range": {
                              "X.datetime": {
                                "gte": "20220101 00:00:00",
                                "lte": "20230901 00:00:00"                          }
                            }
                          }]
                      }
                    }
                  }
                },
                {
               "match": {"pIDo": "СПбГМУ"} 
                }
            ]
          }
        }
      ]
    }
  }
}

# кол-во документов с условием
GET /153/_count
{
} 

# пациенты
GET /153/_search
{"size": 1000, 
  "_source": ["idPatient", "fio", "qqc", "DpFc", "pB", "pJ", "sn", "pIDo"], 
  "query": {
    "bool": {
      "must": [
        {"exists": {
          "field": "pIDo"}}
      ]
    }
  }, 
  "aggs": {
    "cnt": {
      "value_count": {
        "field": "pIDo"
      }
    }
  }, 
  "sort": [
   {
       "idPatient": {
           "order": "asc"
       }
   }
   ]
}

# без фильтра по полю n566
GET /153/_search
{
  "size": 10000,
  "_source": ["idPatient", "pJ"],
  "query": {
      "bool": {
          "must": [
              {
                  "terms": {
                      "idPatient": ["yAGBAWK", "yAGBA\\А", "yAGAJYЕ", "yAGA`и+", "yAGBAaс", "yAGAtыL", "yAGAtыM", "yAGAu\\З", "yAGAg+#", "yAGBAIи", "yAGAg)б", "yAGBAX{", "yAGBAvЖ", "yAGBArт", "yAGAg)с", "yAGAuXS", "yAGADюs", "yAGBAU.", "yAGAg)р", "yAGAAпw", "yAqA]v#", "yAqA]v<", "yAqA]vM", "yAqA]vK", "yAqA]iж", "yAqA]v:", "yAqA]vJ", "yAqA[Fм", "yAqA]v>", "yAqAIbЙ", "yAqA]v2", "yAqA]v+", "yAqA\\(З", "yAqAHВИ", "yAqA\\(Ж", "yAqA]uщ", "yAqAAAA"]
                  }
              },
              {
                  "exists": {
                      "field": "pJ"
                  }
              }
          ]
      }
  },
  "aggs": {
    "cnt_patients": {
      "value_count": {
        "field": "idPatient"
      }
    }
  }
}

# с фильтром по отсутствию поля n566
GET /153/_search
{
  "size": 10000,
  "_source": ["idPatient", "pJ", "n566"],
  "query": {
      "bool": {
          "must": [
              {
                "terms": {
                    "idPatient": ["yAGBAWK", "yAGBA\\А", "yAGAJYЕ", "yAGA`и+", "yAGBAaс", "yAGAtыL", "yAGAtыM", "yAGAu\\З", "yAGAg+#", "yAGBAIи", "yAGAg)б", "yAGBAX{", "yAGBAvЖ", "yAGBArт", "yAGAg)с", "yAGAuXS", "yAGADюs", "yAGBAU.", "yAGAg)р", "yAGAAпw", "yAqA]v#", "yAqA]v<", "yAqA]vM", "yAqA]vK", "yAqA]iж", "yAqA]v:", "yAqA]vJ", "yAqA[Fм", "yAqA]v>", "yAqAIbЙ", "yAqA]v2", "yAqA]v+", "yAqA\\(З", "yAqAHВИ", "yAqA\\(Ж", "yAqA]uщ", "yAqAAAA"]
                }
              },
              {
                  "exists": {
                      "field": "pJ"
                  }
              }
          ],
        "must_not": [
          {
                  "exists": {
                      "field": "n566"
                  }
              }
        ]
      }
  },
  "aggs": {
    "cnt_patients": {
      "value_count": {
        "field": "idPatient"
      }
    }
  }
}

# вывод данных по условиям
GET /153/_search
{ "size": 1000,
  "_source": ["pIDo", "fio", "qqo", "datqq", "DnpG", "sn"],
  "query": {
    "bool": {
      "must_not": [
        {"exists": { "field": "sn"}}],
      "must": [
        {"match": {"pIDo": "ГП№107"}}
      ]
    }
  },
  "aggs": {
    "cnt_not_snils": {
      "value_count": {
        "field": "pIDo"
      }
    }
  }
 }
 
# кол-во документов в 153
GET /153/_count
{}

# маппинг 153
GET /153/_mapping


#######################
# services_showcase_1 #
#######################

Ольга Мурзина, [07.11.2023 13:11]
# удаление витрины
DELETE /services_showcase_1/

# маппинг витрины
GET /services_showcase_1/_mapping

# кол-во записей в общей витрине
GET /services_showcase_1/_count

# 1 уровень полноты данных
GET /services_showcase_1/_search
{ "size": 200,
  "query": {
    "bool": {
      "must_not": [
        {"exists": {
          "field": "idEpisodLong"
          }
        }
      ],
      "must": [
        {"exists": {
          "field": "idPatient"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "idPatient"}
    }
  }
}

# 2 уровень полноты данных
GET /services_showcase_1/_search
{ "size": 200, 
  "query": {
    "bool": {
      "must_not": [
        {"exists": {
          "field": "idServiceLong"
          }
        }
      ],
      "must": [
        {"exists": {
          "field": "idEpisodLong"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "idEpisodLong"}
    }
  }
}

# 3 уровень полноты данных
GET /services_showcase_1/_search
{ "size": 200, 
  "query": {
    "bool": {
      "must_not": [
        {"exists": {
          "field": "idStatusLong"
          }
        }
      ],
      "must": [
        {"exists": {
          "field": "idServiceLong"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "idServiceLong"}
    }
  }
}

# 4 уровень полноты данных
GET /services_showcase_1/_search
{"size": 200, 
  "query": {
    "bool": {
      
      "must": [
        {"exists": {
          "field": "idStatusLong"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "idStatusLong"}
    }
  }
}

# проверка наличия/отсутствия _id = idPatient/idEpisodLong/idServiceLong
GET /services_showcase_1/_search
{"size": 50, 
  "query": {
    "match_phrase": {
      "_id": "yAGBADч"
    }
  }
}

# проверка уникальности idPatient при записях 1 уровня полноты данных
GET /services_showcase_1/_search
{"size": 50, 
  "query": {
    "match_phrase": {
      "idPatient": "yAGARAы"
    }
  }, 
  "sort": [
    {
      "_id": {
        "order": "desc"
      }
    }
  ]
}

# проверка уникальности idEpisodLong при 2 уровне полноты данных
GET /services_showcase_1/_search
{"size": 50, 
  "query": {
    "match_phrase": {
      "idEpisodLong": "yAGA^2(Abo"
    }
  }, 
  "sort": [
    {
      "_id": {
        "order": "desc"
      }
    }
  ]
}

# проверка уникальности idServiceLong при 3 уровне полноты данных
GET /services_showcase_1/_search
{"size": 50,
  "query": {
    "match_phrase": {
      "idServiceLong": "yAGAaЪ#AALAAZNAAйЭA"
    }
  }, 
  "sort": [
    {
      "_id": {
        "order": "desc"
      }
    }
  ]
}

# агрегирующий запрос к витрине по списку ключей на примере idPatient
GET services_showcase_1/_search
{
   "size": 0,
   "query": {
      "bool": {
         "must": {
            "terms": {
               "idPatient": ["yAGBAS;", "uBKAATP", "uBKAAJ8", "dABAAF]", "uBKAAHr"]
            }
         }
      }
   },
   "aggs": {
      "aggregation_name_1": {
         "terms": {
            "size": 10000,
            "field": "idPatient"
         },
         "aggs": {
            "aggregation_name_2": {
               "top_hits": {
                  "size": 1,
                  "_source": ["idPatient", "pJ", "pI", "X.datetime", "sn", "pB", "fio", "partOfdata"]
               }
            }
         }
      }
   }
}

# Запрос к витрине на агрегацию по типу операций

# SQL
GET /_sql?format=txt
{
  "query": 
  """SELECT Mosr type,
            count(idServiceLong) cnt
     FROM services_showcase_1 
     WHERE ((pDatop is not null) and
           (pDatop between 20180101 and 20230101) and
           (pANdop like '%выполнено%') and 
           (tn like '%Операция%') )
    GROUP BY Mosr
    ORDER BY cnt DESC"""
}

Ольга Мурзина, [07.11.2023 13:11]
# DSL
GET /services_showcase_1/_search
{ "size": 100,
"_source": ["idServiceLong", "u","tn", "pANdop", "Mosr", "pDatop", "panv", "pvs"],
"query": {
    "bool": {
        "must": [
          {
            "exists": {"field": "pDatop"}
            },
            {
            "range": {
                "pDatop": {
                    "gte": "20180101",
                    "lte": "20230101"
                }
            }
            },
            {
            "exists": {"field": "panv"}
            },
            {
            "term": {"pANdop": "выполнено"}
            },
            {
            "simple_query_string": {
                "query": "Операция*",
                "fields": ["tn"]}
            }
        ],
        "should": [
          {
            "simple_query_string": {
                "query": "СТАЦИОНАР*",
                "fields": ["pvs"]}
            },
            {
            "simple_query_string": {
                "query": "АКУШЕР*",
                "fields": ["pvs"]}
            }
        ]
    }
},
  "aggs": {
    "all_oper": {
      "terms": {
        "field": "Mosr",
        "size": 10000
      }
    }
  }
}

# запрос к витрине по кол-ву эпизодов клиента

#SQL
GET /_sql?format=txt
{
  "query": 
  """SELECT idPatient,
            count(idEpisodLong) cnt
     FROM services_showcase_1 
     WHERE (pDatop between 20180101 and 20210901)
     GROUP BY idPatient
     HAVING cnt > 7
     ORDER BY cnt desc
     """
}

#DSL

GET /services_showcase_1/_search
{
  "_source": ["idPatient", "idEpisodLong"],
  "query": {
    "bool": {
        "must": [
            {
            "range": {
                "pDatop": {
                    "gte": "20180101",
                    "lte": "20210901"
                }
            }
          }
        ]
    }
  },
  "aggs": {
    "all_episods": {
      "terms": {
        "field": "idPatient",
        "size": 10000
      },
      "aggs": {
        "all_episods": {
          "bucket_selector": {
            "buckets_path": {
              "the_doc_count": "_count"
            },
            "script": "params.the_doc_count > 7"
          }
        }
      }
    }
  }
}

# группировка по уникальным значениям поля pIDo
GET /services_showcase_1/_search
{"size": 0,
  "aggs": {
      "tn": {
          "terms": {
              "field": "pIDo",
              "size": 100
            }
        }
    }
}

# вывод записей за период и существующим полем panv
GET /services_showcase_1/_search
{
  "size": 10000,
  "query": {
      "bool": {
          "must": [
              {
                  "range": {
                      "pDatop": {
                          "gte": "20180101",
                          "lte": "20210901"
                      }
                  }
              },             
              {
                  "exists": {"field": "panv"}
              }
          ]
      }
    }
  }

# вывод записей с существующим полем Mosr
GET /services_showcase_1/_search
{ 
  "query": {
    "bool": {
      "must": [
        {"exists": {
          "field": "Mosr"
          }
        }
      ]}
  }
}
  
# группировка по уникальным значениям поля tn
GET /services_showcase_1/_search
{"size": 0,
  "aggs": {
      "tn": {
          "terms": {
              "field": "tn",
              "size": 100
            }
        }
    }
}

# запрос на кол-во строк с обязательным и отсутствующим полями
GET /services_showcase_1/_search
{
  "query": {
    "bool": {
      
      "must": [
        {"exists": {
          "field": "Du"
        }
        }
      ],
      "must_not": [
        {
        "exists": {
          "field": "composite_key"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "Du"}
    }
  }
}

# запрос на кол-во строк с заданным полем
GET /services_showcase_1/_search
{
  "query": {
    "bool": {
      
      "must": [
        {"exists": {
          "field": "ppoo"
        }
        }
      ]
      }
  },
  "aggs": {
    "count_status": {
      "value_count": {
        "field": "idPatient"}
    }
  }
}

Ольга Мурзина, [07.11.2023 13:11]
# запрос на получение сущствующих id из заданного списка id
GET /services_showcase_1/_search
{"size": 10000,
"_source": "idPatient", 
"query": {
    "bool": {
      "must": [
        {
          "terms": {
            "idPatient": ["yAGBAWK", "yAGBA\\А", "yAGAJYЕ", "yAGA`и+", "yAGBAaс", "yAGAtыL", "yAGAtыM", "yAGAu\\З", "yAGAg+#", "yAGBAIи", "yAGAg)б", "yAGBAX{", "yAGBAvЖ", "yAGBArт", "yAGAg)с", "yAGAuXS", "yAGADюs", "yAGBAU.", "yAGAg)р", "yAGAAпw", "yAqA]v#", "yAqA]v<", "yAqA]vM", "yAqA]vK", "yAqA]iж", "yAqA]v:", "yAqA]vJ", "yAqA[Fм", "yAqA]v>", "yAqAIbЙ", "yAqA]v2", "yAqA]v+", "yAqA\\(З", "yAqAHВИ", "yAqA\\(Ж", "yAqA]uщ", "yAqAAAA"]
          }
        }
      ]
    }
  },
  "aggs": {
    "ids": {
      "terms": {
        "field": "idPatient",
        "size": 10000
      }
    }
  }
}


#######
# 174 #
#######

#
GET /174/_count
{}

#
# вывод записей с заданным полем
GET /174/_search
{
  "query": {
    "bool": {
      "must": [
        {"exists": {
          "field": "pID"
          }
        }
      ]

    }
    },
    "aggs": {
      "all_pID": {
        "value_count": {
          "field": "idEpisodLong"
        }
      }
    }
}

# вывод данных с запросом по списку id
GET 174/_search
{
   "size": 0,
   "query": {
      "bool": {
         "must": {
            "terms": {
               "idPatient": ["yAqAB3C", "yAqAB;ь", "yAqAB<$", "yAGdAPП"]
            }
         }
      }
   },
   "aggs": {
      "aggregation_name_1": {
         "terms": {
            "size": 10000,
            "field": "idPatient"
         },
         "aggs": {
            "aggregation_name_2": {
               "top_hits": {
                  "size": 1,
                  "_source": ["idPatient", "idEpisodLong", "X.datetime", "u", "Du"]
               }
            }
         }
      }
   }
}

# эпизоды
GET /174/_search
{
  "sort": [
    {
      "idPatient": {
        "order": "asc"
      }
    }
  ]
}


#######
# 186 #
#######

# кол-во документов на 186
GET /186/_count
{}
  
# вывод записей с заданным полем
GET /186/_search
{
  "query": {
    "bool": {
      "must": [
        {"exists": {
          "field": "pID"
          }
        }
      ]

    }
    },
    "aggs": {
      "all_pID": {
        "value_count": {
          "field": "idServiceLong"
        }
      }
    }
}

# услуги за период с проверкой доп условий
GET /186/_search
{
  "sort": [
    {
      "idPatient": {
        "order": "asc"
      }
    }
  ]
}

# кол-во документов по условию
 GET /186/_count
 {
  "query": {
      "bool": {
        "filter": [
          {
          "bool": {
              "must": [
                
                {"exists": {"field": "pID"}},
                  {
                  "nested": {
                      "path": "X",
                      "query": {
                          "bool": {
                              "must": [
                                  {
                                  "range": {
                                      "X.datetime": {
                                          "gte": "19700101 00:00:00",
                                          "lte": "20230927 00:00:00"
                                    }
                                  }
                                }
                              ]
                            }
                      }
                  }
                  }
                ]
            }
          }
        ]
      }
    }
 }
 
 
######
# 83 #
######

# категории, субкатегории, услуги
GET /83/_search
{
  "_source": ["idPatient", "u", "Du"],
  "sort": [
    {
      "idPatient": {
        "order": "asc"
      }
    }
  ]
}


#######
# 244 #
#######

# вывод полей с сортировкой
GET /244/_search
{
  "_source": ["idPatient", "Dz", "tsh", "pE", "puR"],
  "sort": [
    {
      "idPatient": {
        "order": "asc"
      }
    }
  ]
}


#######
# 293 #
#######

# вывод полей с сортировкой
GET /293/_search
{
  "_source": ["idPatient", "n1000", "idStatus", "instr"],
  "sort": [
    {
      "idPatient": {
        "order": "asc"
      }
    }
  ]
}

Ольга Мурзина, [07.11.2023 13:11]
GET /293/_search
{"_source": ["idPatient", "idEpisodLong", "idServiceLong"], 
  "query": {
    "bool": {
        "must": [
            
            {
            "exists": {"field": "idStatusLong"}
            }
        ]
    }
},
"aggs": {
  "cnt": {
    "value_count": {
      "field": "idStatusLong"
    }
  }
}
}

GET /293/_count
{}


#################
# yandex_metric #
#################

# статус индекса
HEAD /yandex_metric/

# установить маппинг витрины по яндекс.метрикам
PUT /yandex_metric_new
{
     "settings" : {
        "number_of_shards" : 1    
     },
     "mappings": {
     "properties": {
        "date": {
                "type": "text",
           "fields": {
             "keyword": {
              "type": "keyword",
              "ignore_above": 256
             }
           }
            },
            "unique_id": {
           "type": "text",
           "fields": {
             "keyword": {
              "type": "keyword",
              "ignore_above": 256
             }
           }
        },
            "value": {
                "type": "text",
           "fields": {
             "keyword": {
              "type": "keyword",
              "ignore_above": 256
             }
           }
            }
     },
     
     "dynamic_templates": [
 
    {
     "std_template": {
        "path_match": "*",
        "match": "y*",
        "mapping": {
           "norms": false,
           "type": "keyword",
           "index": true
        },
       "match_mapping_type": "*"
     }
    }
    ]
    }
  }

# запрос на маппинг индекса
GET /yandex_metric_new/_mapping

# кол-во документов в индексе
GET /yandex_metric/_count
{
  "query": {
    "match_all": {}
  }
}

GET /161/_count
