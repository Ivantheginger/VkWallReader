# VkWallReader
Программа позволяет считать все посты на стене некоторого пользователя или сообщества, начиная с указанной даты и заканчивая текущим временем.
Из постов можно собрать и записать в .csv файл следующие данные: 
  - id поста
  - текст
  - приложения (в виде кодов или ссылок)
  - количество приложений
  - количество лайков
  - количество репостов
  - количество комментариев
 
Также можно вывести графики изменения по часам/дням/месяцам/годам следующих величин:
  - количество постов
  - среднее количество лайков за пост
  - среднее количество репостов за пост
  - среднее количество комментариев за пост

Для работы программы необходим python 3.6 или новее и библиотеки datetime, time, requests, json, csv, matplotlib, tkinter
После запуска файла появится окно с интерфейсом в котором можно отметить интересующие данные, дату, домен пользователя или сообщества и т.д.
После этого просто жмите "Запуск!".

Перед тем как запустить очередное считывание данных, необходимо дождаться окончания работы программы и закрыть все окна с графиками.