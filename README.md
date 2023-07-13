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

