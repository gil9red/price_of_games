#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# TODO: окно фильтра выровнять в ширину таблицы
# TODO: окну фильтра добавить кнопку очищения его


def statistic_string(games):
    """
    Функция возвращает строку с статистикой: сколько всего игр, сколько имеют цены, и процент.
    Пример: (0 / 160 (0%))

    """

    price_number = len([(name, price) for name, price in games if price is not None])
    number = len(games)

    return '({} / {} ({:.0f}%))'.format(
        price_number,
        number,
        (price_number / number * 100) if number > 0 else 0
    )


def total_price(games):
    """
    Функция подсчитает и вернет сумму цен игр в списке.

    """

    def get_price(price):
        """Функция удаляет из получаемое строки все символы кроме цифровых и точки."""

        try:
            price = float(price)
        except Exception as e:
            print('Произошла ошибка, цена не будет участвовать в сумме')
            print(e)
            import traceback
            print(traceback.format_exc())
            price = 0

        return price

    total = sum(get_price(price) for _, price in games if price is not None)

    # Чтобы избавиться от пустой дробной части: 50087.0 -> 50087
    return total if total != int(total) else int(total)


from flask import Flask, render_template_string, request
app = Flask(__name__)

import logging
logging.basicConfig(level=logging.DEBUG)


def round_price(value):
    try:
        # Попытка избавиться от нуля справа, например: 50087.0 -> 50087
        if int(value) == value:
            return int(value)
        else:
            return '{:.2f}'.format(value)
    except:
        return '{:.2f}'.format(value)

app.jinja_env.globals.update(round_price=round_price)


INDEX_HTML_TEMPLATE = '''\
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta content='text/html; charset=UTF-8' http-equiv='Content-Type'/>
    <title>Список игр</title>

    <style type="text/css">
        /* Увеличим заголовок таблиц */
        table > caption {
            font-size: 150%;
        }

        th {
            font-size: 120%;
        }

        #info_table {
            width: 40%;
            border: 0px double #333; /* Рамка вокруг таблицы */
            border-collapse: separate; /* Способ отображения границы */
            border-spacing: 0px; /* Расстояние между ячейками */
        }

        #info_table td {
            padding: 1px; /* Поля вокруг текста */
            border: 0px; /* Граница вокруг ячеек */
        }

        /* Небольшой отступ внутри ячеек */
        td, th {
            padding: 5px;
        }

        .price_is_none {
            background-color: lightgray;
        }

        #top_right_fixed_panel {
            position: fixed; /* Фиксированное положение */
            right: 10px; /* Расстояние от правого края окна браузера */
            top: 10px; /* Расстояние сверху */
            width: 25%;
            padding: 10px; /* Поля вокруг текста */
            background: lightgray; /* Цвет фона */
            border: 1px solid black; /* Параметры рамки */
        }

        #form_set_price_error, #form_rename_game_error, #form_check_price_error  {
            color: red;
        }

        #top_right_fixed_panel input[type="text"] {
            width: 100%;
        }

        .input_search {
            width: 70%;
            font-size: 16px; /* Increase font-size */
        }

        .table_caption {
            width: 70%;
            font-size: 150%; /* Размер шрифта в процентах */
            text-align: center;
        }

        /* Для добавления отступов между заголовком таблицы, input поиска и самой таблицы */
        .block_caption_search > div {
            margin-bottom: 7px;
        }

        #back-top {
            position: fixed;
            bottom: 10px;
            right: 10px;
        }
        #back-top a {
            width: 100px;
            color: black;
            display: block;
            background-color: lightgray;
            text-align: center;
            font: 20px/100% Arial, Helvetica, sans-serif;
            text-decoration: none;
            -webkit-transition: 1s;
            -moz-transition: 1s;
            transition: 1s;
            line-height: 30px;
            -webkit-border-radius: 10px;
            border-radius: 10px;
        }
        #back-top a:hover {
            background-color: gray;
        }

    </style>
</head>

<body id="top">
    <p id="back-top">
        <a href="#top"><span></span>Наверх</a>
    </p>

    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.3/jquery.min.js"></script>
    <script>
    $(document).ready(function(){
        // hide #back-top first
        $("#back-top").hide();

        // fade in #back-top
        $(function () {
            $(window).scroll(function () {
                if ($(this).scrollTop() > 100) {
                    $('#back-top').fadeIn();
                } else {
                    $('#back-top').fadeOut();
                }
            });

            // scroll body to 0px on click
            $('#back-top a').click(function () {
                $('body,html').animate({
                    scrollTop: 0
                }, 800);
                return false;
            });
        });

    });
    </script>


    {% if has_duplicates %}
         <p><font size="20" color="red">АХТУНГ! Найдены дубликаты!</font></p>
    {% endif %}

    Последнее обновление было: {{ last_run_date }}
    <br><br>

    <table id="info_table">
        <tr>
            <td>Итого по пройденным играм:</td><td>{{ round_price(total_price_finished_games) }} руб.</td>
            <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>Пройденных игр:</td><td>{{finished_games|length}}</td>
        </tr>
        <tr>
            <td>Итого по просмотренным играм:</td><td>{{ round_price(total_price_finished_watched_games) }} руб.</td>
            <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>Просмотренных игр:</td><td>{{finished_watched_games|length}}</td>
        </tr>
        <tr>
            <td>Общая сумма:</td><td>{{ round_price(total_price_finished_games + total_price_finished_watched_games) }} руб.</td>
            <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>Всего игр:</td><td>{{finished_games|length + finished_watched_games|length}}</td>
        </tr>
    <table>
    <br>

    <div id="top_right_fixed_panel">
        <form onsubmit="return checkSetPriceForm(this)" method="post" action="/set_price">
            <b>Установка цены у игры:</b>
            <p>Название:<input id="form_name" type="text" name="name"></p>
            <p>Цена:<input id="form_price" type="text" name="price"></p>
            <p><input type="submit" value="Установить цену"></p>
            <p id="form_set_price_error"></p>
        </form>

        <hr>
        <form onsubmit="return checkRenameGameForm(this)" method="post" action="/rename_game">
            <b>Изменение названия игры:</b>
            <p>Старое название:<input id="form_old_name" type="text" name="old_name"></p>
            <p>Новое название:<input id="form_new_name" type="text" name="new_name"></p>
            <p><input type="submit" value="Изменить название"></p>
            <p id="form_rename_game_error"></p>
        </form>

        <hr>
        <form onsubmit="return checkCheckPriceForm(this)" method="post" action="/check_price">
            <b>Вызов проверки цены у игры:</b>
            <p>Название игры:<input id="form_check_price" type="text" name="name"></p>
            <p><input type="submit" value="Проверить цену"></p>
            <p id="form_check_price_error"></p>
        </form>

        <hr>
        <form action="/check_price_all_non_price_games">
            <b>Вызов проверки цены у всех игр без цены:</b>
            <p><input type="submit" value="Проверить цены всех игр"></p>
        </form>

        <hr>
            <button onclick="document.location.href='#finished_game_caption_table'">Перейти к таблице пройденных игр</>
            <button onclick="document.location.href='#finished_watched_game_caption_table'">Перейти к таблице просмотренных игр</>
        </hr>

        <script type="text/javascript">
            function checkSetPriceForm(form) {
                var form_error = document.getElementById('form_set_price_error');

                if (document.getElementById('form_name').value == ""
                        || document.getElementById('form_price').value == "") {
                    form_error.innerHTML = "Все поля нужно заполнять!";
                    return false;
                }
                form_error.innerHTML = "";

                return true;
            };

            function checkRenameGameForm(form) {
                var form_error = document.getElementById('form_rename_game_error');
                var old_name = document.getElementById('form_old_name').value;
                var new_name = document.getElementById('form_new_name').value;

                if (old_name == "" || new_name == "") {
                    form_error.innerHTML = "Все поля нужно заполнять!";
                    return false;

                } else if (old_name == new_name) {
                    form_error.innerHTML = "Новое имя не должно совпадать со старым!";
                    return false;
                }

                form_error.innerHTML = "";

                return true;
            };

            function checkCheckPriceForm(form) {
                var form_error = document.getElementById('form_check_price_error');
                var name = document.getElementById('form_check_price').value;

                if (name == "") {
                    form_error.innerHTML = "Все поля нужно заполнять!";
                    return false;
                }

                form_error.innerHTML = "";

                return true;
            };

        </script>
    </div>

    <form>
        <input id="radio_show_all_games" name="radio_show_game" type="radio" onclick="common_filter()" checked> Показывать все игры</input><br>
        <input id="radio_show_games_with_price" name="radio_show_game" type="radio" onclick="common_filter()"> Показывать игры с ценой</input><br>
        <input id="radio_show_games_without_price" name="radio_show_game" type="radio" onclick="common_filter()"> Показывать игры без цены</input>
    </form>

    <div id="finished_game_caption_table" class="block_caption_search">
        <div class="table_caption">Пройденные игры {{ finished_game_statistic }}</div>
        <div>
            <input type="search" id="input_finished_game" class="input_search" onkeyup="common_filter()" placeholder="Поиск игр...">
        </div>
    </div>
    <table id="finished_game" width="70%" border="1">
        <colgroup>
           <col span="1" style="width: 80%;">
           <col span="1" style="width: 20%;">
        </colgroup>

        <tr>
        {% for header in headers %}
            <th>{{ header }}</th>
        {% endfor %}
        </tr>

        {% for name, price in finished_games %}
            {% if price %}
                <tr class="game_row">
                    <td>{{ name }}</td>
                    <td>{{ price }}</td>
                </tr>
            {% else %}
                <tr class="game_row price_is_none">
                    <td>{{ name }}</td>
                    <td>{{ UNKNOWN_PRICE_TITLE }}</td>
                </tr>
            {% endif %}
        {% endfor %}

        <tr><td align="right">Итого:</td><td>{{ round_price(total_price_finished_games) }}</td></tr>
    </table>
    <br><br><br>

    <div id="finished_watched_game_caption_table" class="block_caption_search">
        <div class="table_caption">Просмотренные игры {{ finished_watched_game_statistic }}</div>
        <div>
            <input type="search" id="input_finished_watched_game" class="input_search" onkeyup="common_filter()" placeholder="Поиск игр...">
        </div>
    </div>
    <table id="finished_watched_game" width="70%" border="1">
        <colgroup>
           <col span="1" style="width: 80%;">
           <col span="1" style="width: 20%;">
        </colgroup>

        <tr>
        {% for header in headers %}
            <th>{{ header }}</th>
        {% endfor %}
        </tr>

        {% for name, price in finished_watched_games %}
            {% if price %}
                <tr class="game_row">
                    <td>{{ name }}</td>
                    <td>{{ price }}</td>
                </tr>
            {% else %}
                <tr class="game_row price_is_none">
                    <td>{{ name }}</td>
                    <td>{{ UNKNOWN_PRICE_TITLE }}</td>
                </tr>
            {% endif %}
        {% endfor %}

        <tr><td align="right">Итого:</td><td>{{ round_price(total_price_finished_watched_games) }}</td></tr>
    </table>

    <script>
        // Функция перебирает строки таблицы оценивает их, и если они не подходит прячет, иначе добавляет в список.
        // Цель -- фильтр таблицы и заполнение списка строками, оставшимися видимыми после фильтра
        function fill_list_from_rows(rows, list) {
            var is_radio_show_all_games_checked = document.getElementById('radio_show_all_games').checked;
            var is_radio_show_games_with_price_checked = document.getElementById('radio_show_games_with_price').checked;
            var is_radio_show_games_without_price_checked = document.getElementById('radio_show_games_without_price').checked;

            for (var i = 0; i < rows.length; i++) {
                var tr = rows[i];

                if (is_radio_show_all_games_checked) {
                    list.push(tr);

                } else if (is_radio_show_games_with_price_checked) {
                    // Если цена не указана и хотим видить игры с ценой
                    if (tr.classList.contains("price_is_none")) {
                        tr.style.display = "none";
                    } else {
                        list.push(tr);
                    }

                } else if (is_radio_show_games_without_price_checked) {
                    // Если цена указана и хотим видить игры без ценой
                    if (!tr.classList.contains("price_is_none")) {
                        tr.style.display = "none";
                    } else {
                        list.push(tr);
                    }
                }
            }
        }

        // Функция перебирает элементы в списке и ищет в них строку, если не найдено, прячет их строку
        function filter_rows_by_text(text, rows) {
            // Если значение в фильтре есть, есть смысл перебора строк для вторичной фильтрации
            if (text != "") {
                text = text.toLowerCase();

                rows.forEach(function(tr) {
                    // Перебор ячеек таблицы
                    var td_list = tr.getElementsByTagName("td");

                    // Строка, содержащая значения ячеек текущей строки
                    var tr_text = "";
                    for (var i = 0; i < td_list.length; i++) {
                        tr_text += td_list[i].innerHTML.toLowerCase();
                    }

                    // Если нашли строку фильтра, то делаем строку видимой и прерываем перебор ячеек
                    // (если строка фильтра пустая, то поиск вернет 0 индекс, что говорит, что строка нашлась)
                    if (tr_text.indexOf(text) == -1) {
                        tr.style.display = "none";
                    }
                });
            }
        }

        function common_filter() {
            var finished_game_table = document.getElementById('finished_game');
            var finished_watched_game_table = document.getElementById('finished_watched_game');

            var finished_game_table_rows = finished_game_table.getElementsByClassName('game_row');
            var finished_watched_game_table_rows = finished_watched_game_table.getElementsByClassName('game_row');

            // Сначала нужно сделать все строки таблицы видимыми
            for (var i = 0; i < finished_game_table_rows.length; i++) {
                finished_game_table_rows[i].style.display = "";
            }
            for (var i = 0; i < finished_watched_game_table_rows.length; i++) {
                finished_watched_game_table_rows[i].style.display = "";
            }

            // Теперь применим первичный фильтр -- по наличию цены: все игры, с ценой и без цены
            var filter_finished_game_table_rows = [];
            var filter_finished_watched_game_table_rows = [];

            // Скрытие строк по фильтру и заполнение списка оставшимися строками
            fill_list_from_rows(finished_game_table_rows, filter_finished_game_table_rows);
            fill_list_from_rows(finished_watched_game_table_rows, filter_finished_watched_game_table_rows);

            // Вторичный фильтр по тексту
            var input_finished_game_value = document.getElementById('input_finished_game').value;
            filter_rows_by_text(input_finished_game_value, filter_finished_game_table_rows);

            var input_finished_watched_game_value = document.getElementById('input_finished_watched_game').value;
            filter_rows_by_text(input_finished_watched_game_value, filter_finished_watched_game_table_rows);
        }

        // Сразу вызовим, т.к. браузер помнит состояние фильтров между обновлениями страницы
        common_filter();

    </script>
</body>
</html>
'''


@app.route("/")
def index():
    from common import FINISHED, FINISHED_WATCHED, create_connect, settings, get_duplicates
    connect = create_connect()

    try:
        cursor = connect.cursor()

        get_game_sql = '''
            SELECT name, price
            FROM game
            WHERE kind = ?
            ORDER BY name
        '''
        finished_games = cursor.execute(get_game_sql, (FINISHED,)).fetchall()
        finished_watched_games = cursor.execute(get_game_sql, (FINISHED_WATCHED,)).fetchall()

    finally:
        connect.close()

    return render_template_string(
        INDEX_HTML_TEMPLATE,
        headers=['Название', 'Цена (руб.)'],
        finished_games=finished_games, finished_watched_games=finished_watched_games,
        finished_game_statistic=statistic_string(finished_games),
        finished_watched_game_statistic=statistic_string(finished_watched_games),
        total_price_finished_games=total_price(finished_games),
        total_price_finished_watched_games=total_price(finished_watched_games),
        last_run_date=settings.last_run_date,
        has_duplicates=bool(get_duplicates()),
        UNKNOWN_PRICE_TITLE='Цена не задана',
    )


@app.route("/set_price", methods=['POST'])
def set_price():
    """
    Функция устанавливает цену для указанной игры.

    """

    if request.method == 'POST':
        print(request.form)

        if 'name' in request.form and 'price' in request.form:
            name = request.form['name']
            price = request.form['price']
            print(name, price)

            from common import set_price_game
            set_price_game(name, price)

    from flask import redirect
    return redirect("/")


@app.route("/rename_game", methods=['POST'])
def rename_game():
    """
    Функция изменяет название игры.
    Используется после изменения названия игры в гистах.

    """

    if request.method == 'POST':
        print(request.form)

        if 'old_name' in request.form and 'new_name' in request.form:
            old_name = request.form['old_name']
            new_name = request.form['new_name']
            print(old_name, new_name)

            from common import rename_game
            rename_game(old_name, new_name)

    from flask import redirect
    return redirect("/")


@app.route("/check_price", methods=['POST'])
def check_price():
    """
    Функция запускает проверку цены у указанной игры.

    """

    if request.method == 'POST':
        print(request.form)

        if 'name' in request.form:
            name = request.form['name']
            print(name)

            from common import check_and_fill_price_of_game
            check_and_fill_price_of_game(name)

    from flask import redirect
    return redirect("/")


@app.route("/check_price_all_non_price_games")
def check_price_all_non_price_games():
    """
    Функция принудительной проверки цен всех игр для которых не получилось найти цену.

    """

    from common import check_price_all_non_price_games
    check_price_all_non_price_games()

    from flask import redirect
    return redirect("/")


if __name__ == '__main__':
    # Localhost
    app.debug = True

    app.run(
        port=5000,

        # NOTE: убрал т.к. вызывало при получении запроса ошибку "sqlite3.ProgrammingError: SQLite objects created
        # in a thread can only be used in that same thread.The object was created in thread id 9284 and this is"
        # а разбираться с этим не было желания
        #
        # # Включение поддержки множества подключений
        # threaded=True,
    )

    # # Public IP
    # app.run(host='0.0.0.0')
