#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# TODO: кнопки перемещения к таблицам (пусть на панели справа будут)
# TODO: кнопки перемещения к началу и концу страницы (пусть на панели справа будут)
# TODO: правильно отобюражать сумму с копейками
# TODO: после клика на кнопки показа игр применять фильтр


# NOTE: вычисление такого можно было перенести на клиента и описать через javascript
# но т.к. данных мало и пользоваться ими будут очень редко, можно на серверной стороне
# их считать.
# Это будет касаться и подсчета сумм.
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


INDEX_HTML_TEMPLATE = '''\
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
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

    </style>
</head>
<body>
    {% if has_duplicates %}
         <p><font size="20" color="red">АХТУНГ! Найдены дубликаты!</font></p>
    {% endif %}

    Последнее обновление было: {{ last_run_date }}
    <br><br>

    <table id="info_table">
        <tr>
            <td>Итого по пройденным играм:</td><td>{{ total_price_finished_games }} руб.</td>
            <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>Пройденных игр:</td><td>{{finished_games|length}}</td>
        </tr>
        <tr>
            <td>Итого по просмотренным играм:</td><td>{{ total_price_finished_watched_games }} руб.</td>
            <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>Просмотренных игр:</td><td>{{finished_watched_games|length}}</td>
        </tr>
        <tr>
            <td>Общая сумма:</td><td>{{ total_price_finished_games + total_price_finished_watched_games }} руб.</td>
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

    <div style="width:300px">
        <button style="width:100%" onclick="show_all_games()">Показывать все игры</button>
        <button style="width:100%" onclick="show_games_with_price()">Показывать игры с ценой</button>
        <button style="width:100%" onclick="show_games_without_price()">Показывать игры без цены</button>
    </div>

    <div class="block_caption_search">
        <div class="table_caption">Пройденные игры {{ finished_game_statistic }}</div>
        <div>
            <input type="text" id="input_finished_game" class="input_search" onkeyup="filter_table('input_finished_game', 'finished_game')" placeholder="Поиск игр...">
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

        <tr><td align="right">Итого:</td><td>{{ total_price_finished_games }}</td></tr>
    </table>
    <br><br><br>

    <div class="block_caption_search">
        <div class="table_caption">Просмотренные игры {{ finished_watched_game_statistic }}</div>
        <div>
            <input type="text" id="input_finished_watched_game" class="input_search" onkeyup="filter_table('input_finished_watched_game', 'finished_watched_game')" placeholder="Поиск игр...">
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

        <tr><td align="right">Итого:</td><td>{{ total_price_finished_watched_games }}</td></tr>
    </table>

    <script>
        function show_all_games() {
            var tr_list = document.getElementsByClassName('game_row');

            // Перебор строк таблицы
            for (var i = 0; i < tr_list.length; i++) {
                var tr = tr_list[i];
                tr.style.display = "";
            }
        }

        function show_games_with_price() {
            var tr_list = document.getElementsByClassName('game_row');

            // Перебор строк таблицы
            for (var i = 0; i < tr_list.length; i++) {
                var tr = tr_list[i];

                // Если цена не указана и хотим видить игры с ценой
                if (tr.classList.contains("price_is_none")) {
                    tr.style.display = "none";
                } else {
                    tr.style.display = "";
                }
            }
        }

        function show_games_without_price() {
            var tr_list = document.getElementsByClassName('game_row');

            // Перебор строк таблицы
            for (var i = 0; i < tr_list.length; i++) {
                var tr = tr_list[i];

                // Если цена указана и хотим видить игры без ценой
                if (!tr.classList.contains("price_is_none")) {
                    tr.style.display = "none";
                } else {
                    tr.style.display = "";
                }
            }
        }

        // Функция для фильтрации строк указанной таблицы
        function filter_table(input_id, table_id) {
            var filter_text = document.getElementById(input_id).value.toLowerCase();
            var table = document.getElementById(table_id);
            var tr_list = table.getElementsByTagName("tr");

            // Перебор строк таблицы
            for (var i = 0; i < tr_list.length; i++) {
                var tr = tr_list[i];

                // Перебор ячеек таблицы
                var td_list = tr.getElementsByTagName("td");
                for (var j = 0; j < td_list.length; j++) {
                    var value = td_list[j].innerHTML.toLowerCase();

                    // Если нашли, то делаем строку видимой и прерываем перебор ячеек
                    if (value.indexOf(filter_text) != -1) {
                        tr.style.display = "";
                        break;

                    } else {
                        tr.style.display = "none";
                    }
                }
            }
        }

        // Если в input'ах уже что-то будет, таблицы нужно будет показать отфильтрованными
        filter_table('input_finished_game', 'finished_game');
        filter_table('input_finished_watched_game', 'finished_watched_game');

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
        UNKNOWN_PRICE_TITLE='Неизвестная цена',
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
