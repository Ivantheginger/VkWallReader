import datetime
import requests
import json
import csv
import matplotlib.pyplot as plt
import time
from tkinter import *
from tkinter import ttk
from tkinter.ttk import Combobox
from tkinter import messagebox


def get_data(date, domain):
    """Получает данные из ВК в виде json и возвращает list из dict'ов, которые представляют посты."""
    # Получил создав своё приложение в vk.com/dev
    access_token = ''
    param = {
        'count': 100,
        'offset': 1,
        'domain': domain,
        'access_token': access_token,
        'v': 5.101
    }
    post_date = date
    url = F"https://api.vk.com/method/wall.get?"

    session = requests.Session()
    posts = []
    # Вытаскиваем по 100 постов и добавляем их к posts, пока очередной пост не окажется позднее заданной date
    while post_date >= date:

        vk_data = session.post(url, param)
        time1 = datetime.datetime.now()
        # ВК возвращает json
        posts_dict = json.loads(vk_data.text)
        # Если профиль закрыт или заблокирован, будем иметь 'error' в ключах возвращаемого json
        # Поднимаем исключение, обрабатываем его уже в основном процессе Tkinter
        if 'error' in posts_dict:
            print(posts_dict['error']['error_msg'])
            raise ValueError(posts_dict['error']['error_msg'])

        posts_dict = posts_dict['response']['items']

        # Если постов больше нет прерываем цикл
        if not posts_dict:
            break

        for item in posts_dict:
            post_date = item['date']
            if post_date < date:
                break
            posts += [item]

        param['offset'] += 100
        # Вк имеет ограничение по запросам - 3 запроса в секунду. Засекаем время до запроса и перед очередным запросом
        # и если прошло менее трети секунды, ждем пока время между запросами не будет чуть более трети секунды
        if (datetime.datetime.now() - time1).microseconds / 1000000.0 < 0.34:
            time.sleep(0.35 - (datetime.datetime.now() - time1).microseconds / 1000000.0)

        print(F"Постов собрано:", len(posts))

    if posts and 'is_pinned' in posts[0] and posts[0]['is_pinned']:
        posts.pop(0)
    return posts


# Кладем данные в csv файл
def put_data_to_csv(posts, flags, domain, filename=''):
    """Кладет данные в csv файл. В flags указываются необходимые поля данных."""
    names = ['id', 'text', 'attachments', 'attachments count', 'likes count', 'reposts count', 'comments count']
    keys = []
    # Сохраняем те поля данных, которые указаны в flags
    for name in names:
        if flags[name]:
            keys.append(name)

    if not filename:
        filename = f'{domain} {datetime.datetime.now().date()} VK data.csv'
    else:
        filename += '.csv'

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        # Пишем именя полей
        csvwriter = csv.writer(csvfile, quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(keys)

        # Для каждого поста вытаскиваем только затребованные данные и записываем их в том же порядке, что и имена полей
        for post in posts:
            row = []
            if 'id' in keys:
                row.append(post['id'])
            if 'text' in keys:
                row.append(post['text'])

            if 'attachments' in keys:
                row.append('')
                if 'attachments' in post:

                    for att in post['attachments']:
                        if att['type'] == 'photo':
                            max_size = att[att['type']]['sizes'][0]
                            for size in att[att['type']]['sizes']:
                                if max_size['width'] <= size['width'] and max_size['height'] <= size['height']:
                                    max_size = size

                            row[-1] += max_size['url'] + ' '

                        elif 'url' in att[att['type']]:
                            row[-1] += att[att['type']]['url'] + ' '

                        elif 'track_code' in att[att['type']]:
                            row[-1] += att[att['type']]['track_code'] + ' '

                        else:
                            row[-1] += str(att[att['type']]['id']) + ' '

                if 'attachments count' in keys:
                    if 'attachments' in post:
                        row.append(len(post['attachments']))
                    else:
                        row.append(0)
                if 'likes count' in keys:
                    row.append(post['likes']['count'])
                if 'reposts count' in keys:
                    row.append(post['reposts']['count'])
                if 'comments count' in keys:
                    row.append(post['comments']['count'])

            csvwriter.writerow(row)


def get_interval(interval, date):
    """Функция выдающая номер интервала, используется для отделения постов по интервалам"""
    if interval == 'hour':
        return date.hour
    elif interval == 'day':
        return date.day
    elif interval == 'month':
        return date.month
    elif interval == 'year':
        return date.year


def get_first_second(interval, date):
    """Выдает начало интервала в виде datetime объекта"""
    if interval == 'hour':
        return datetime.datetime(date.year, date.month, date.day, date.hour, 0)
    elif interval == 'day':
        return datetime.datetime(date.year, date.month, date.day, 0, 0)
    elif interval == 'month':
        return datetime.datetime(date.year, date.month, 1, 0, 0)
    elif interval == 'year':
        return datetime.datetime(date.year, 1, 1, 0, 0)


def show_stats(posts, keys, interval):
    """ Рисует графики изменения количества данных
    указанынх в keys : list разбивая на интервалы длинной interval : str"""
    y = {key: [] for key in keys}
    date = datetime.datetime.utcfromtimestamp(posts[0]['date'])
    xdates = []
    ycounts = {key: 0 for key in keys}
    post_counter = 0
    for post in posts:
        post_counter += 1
        # Условие проходит если начался следующий интервал, сохраняем подсчитанные данные
        if get_interval(interval, datetime.datetime.utcfromtimestamp(post['date'])) != get_interval(interval, date):
            for key in keys:
                if key == 'posts':
                    y[key].append(ycounts[key])
                else:
                    y[key].append(ycounts[key] / float(post_counter))

            xdates.append(get_first_second(interval, date))
            date = datetime.datetime.utcfromtimestamp(post['date'])
            ycounts = {key: 0 for key in keys}
            post_counter = 0

        # Подсчитываем количество на текущем интервале
        for key in keys:
            if key == 'posts':
                ycounts['posts'] += 1
            else:
                ycounts[key] += post[key]['count']

    # Дописываем данные с последнего интервала
    if post_counter:
        for key in keys:
            if key == 'posts':
                y[key].append(ycounts[key])
            else:
                y[key].append(ycounts[key] / float(post_counter))
        xdates.append(get_first_second(interval, date))

    # Рисуем графики
    colors = ('b', 'r', 'g', 'c')
    for key in keys:
        plt.plot_date(xdates, y[key], 'b', tz=datetime.timezone.utc,
                      xdate=True, color=colors[keys.index(key)])
        plt.xlabel('Date')

    plt.legend(keys, loc=2)
    plt.show()


if __name__ == "__main__":
    def process():
        """Функция запускаемая нажатием клавиши 'Запуск!' в интерфейсе. Проверяет корректность введенных в GUI данных,
        считывает выбранные чекбоксы и вписанные данные из GUI, и вызывает get_data(), put_data_to_csv(), show_stats()
        с соответствующими аргументами"""
        if chk_csv_state.get() or graph_chk_state.get():
            try:
                date = datetime.datetime(int(year.get()), int(month.get()), int(day.get()))
                date = date.replace(tzinfo=datetime.timezone.utc).timestamp()
            except(ValueError, OverflowError):
                messagebox.showinfo('Ошибка', 'Некорректная дата.\nПример корректной даты для 28-го июня '
                                              '2019-го года: 2019 6 28. ')
                return 1

            if file_name.get() and chk_csv_state.get():
                try:
                    f = open(file_name.get() + '.csv', 'w', newline='', encoding='utf-8')
                    f.close()
                except OSError:
                    messagebox.showinfo('Ошибка', 'Некорректное имя файла.\nНе указывайте .csv в конце.\n'
                                                  'Не используйте запрещенные символы в имени файла.\n'
                                                  'Если Вы указываете полный путь, укажите в конце имя файла'
                                                  ' ...\\name\n'
                                                  'Вы можете оставить это поле пустым, имя файла'
                                                  ' будет установлено по умолчанию. ')
                    return 1

            try:
                posts = get_data(date, domain.get())
            except ValueError:
                messagebox.showinfo('Ошибка', 'Некорректный домен или профиль закрыт или заблокирован')
                return 1

            if not posts:
                messagebox.showinfo('Ошибка', 'Нет постов начиная с указанной даты')
                return 1

        if chk_csv_state.get():
            csv_flags_names = ('id', 'text', 'attachments', 'attachments count',
                               'likes count', 'reposts count', 'comments count')

            csv_flags_translation = {csv_checkboxes_names[i]: csv_flags_names[i] for i in range(len(csv_flags_names))}
            flags = {csv_flags_names[i]: 0 for i in range(len(csv_flags_names))}
            anything_to_collect = 0
            for key in csv_checkboxes:
                if csv_checkboxes[key].get():
                    flags[csv_flags_translation[key]] = 1
                    anything_to_collect = 1
            if anything_to_collect:
                put_data_to_csv(posts, flags, domain.get(), file_name.get())

        if graph_chk_state.get():
            key_names = ('posts', 'likes', 'reposts', 'comments')
            graph_keys_translation = {graph_names[i]: key_names[i] for i in range(len(key_names))}
            keys = []
            anything_to_collect = 0
            for key in graph_checkboxes:
                if graph_checkboxes[key].get():
                    keys.append(graph_keys_translation[key])
                    anything_to_collect = 1

            if anything_to_collect:
                interval_names = ('Час', 'День', 'Месяц', 'Год')
                interval_names_eng = ('hour', 'day', 'month', 'year')
                interval_names_translation = {interval_names[i]: interval_names_eng[i]
                                              for i in range(len(interval_names))}
                show_stats(posts, keys, interval_names_translation[combo.get()])


    # Рисуем интерфейс

    window = Tk()
    window.title("VK wall reader")

    lbldomain = Label(window, text="Домен пользователя  или сообщества vk.com/", font=("Arial", 10))
    lbldomain.grid(column=0, row=0)
    domain = Entry(window, width=10)
    domain.insert(END, 'vkteam')
    domain.grid(column=0, row=1)

    lbldate = Label(window, text="Дата, с которой считывать данные:", font=("Arial", 10))
    lbldate.grid(column=1, row=1)

    year = Entry(window, width=10)
    year.insert(END, 2019)
    year.grid(column=2, row=1)
    month = Entry(window, width=10)
    month.insert(END, 1)
    month.grid(column=3, row=1)
    day = Entry(window, width=10)
    day.insert(END, 1)
    day.grid(column=4, row=1)

    y_lbl = Label(window, text="Год", font=("Arial", 10))
    y_lbl.grid(column=2, row=0)
    m_lbl = Label(window, text="Месяц", font=("Arial", 10))
    m_lbl.grid(column=3, row=0)
    d_lbl = Label(window, text="День", font=("Arial", 10))
    d_lbl.grid(column=4, row=0)

    ttk.Separator(window, orient=HORIZONTAL).grid(row=2, columnspan=10, sticky="ew")

    chk_csv_state = BooleanVar()
    chk_csv_state.set(True)
    chk_csv = Checkbutton(window, var=chk_csv_state, text="Сбор данных в .csv", font=("Arial", 13))
    chk_csv.grid(column=0, row=3)

    lbl_file = Label(window, text="Имя файла:")
    lbl_file.grid(column=2, row=3)
    file_name = Entry(window, width=10)
    file_name.grid(column=3, row=3)

    lbl_flags = Label(window, text="Данные", font=("Arial", 10))
    lbl_flags.grid(column=0, row=4)

    csv_checkboxes_names = ['id', 'текст', 'приложения', 'кол-во приложений', 'кол-во лайков', 'кол-во репостов',
                            'кол-во комментариев']
    csv_checkboxes = {}
    for i, name in enumerate(csv_checkboxes_names):
        state_var = BooleanVar()
        state_var.set(True)
        chk = Checkbutton(window, var=state_var, text=name)
        csv_checkboxes.update({name: state_var})
        chk.grid(column=0, row=5 + i)

    ttk.Separator(window, orient=HORIZONTAL).grid(row=15, columnspan=10, sticky="ew")

    graph_chk_state = BooleanVar()
    graph_chk_state.set(True)
    graph_chk = Checkbutton(window, var=graph_chk_state, text="Графики", font=("Arial", 13))
    graph_chk.grid(column=0, row=16)

    lbl_interval = Label(window, text="Временной интервал", font=("Arial", 10))
    lbl_interval.grid(column=1, row=17)
    combo = Combobox(window, state="readonly")
    combo['values'] = ('Час', 'День', 'Месяц', 'Год')
    combo.current(1)
    combo.grid(column=1, row=18)

    lbl_graph_keys = Label(window, text="Данные", font=("Arial", 10))
    lbl_graph_keys.grid(column=0, row=17)

    graph_names = ('Посты', 'Лайки', 'Репосты', 'Комментарии')
    graph_checkboxes = {}
    for i, name in enumerate(graph_names):
        graph_chk_var = BooleanVar()
        if name == 'Лайки':
            graph_chk_var.set(True)
        chk = Checkbutton(window, var=graph_chk_var, text=name)
        graph_checkboxes.update({name: graph_chk_var})
        chk.grid(column=0, row=18 + i)

    ttk.Separator(window, orient=HORIZONTAL).grid(row=24, columnspan=10, sticky="ew")

    btn = Button(window, text="Запуск!", height=2, width=20, command=process)
    btn.grid(column=1, row=25)

    window.mainloop()
