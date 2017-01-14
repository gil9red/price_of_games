#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


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

    def get_price(price_title):
        """Функция удаляет из получаемое строки все символы кроме цифровых и точки."""

        # TODO: быстрый вариант решения проблемы, но не надежный
        price = price_title.replace(' pуб.', '').strip()

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


# TODO: добавить форму переименования игры. Если игра будет изменена гистах, то ее
# название нужно будет изменить и в базе скрипта. Второй способ очищения базы и
# повторный поиск всех игр кажется неудобным

@app.route("/")
def index():
    from common import FINISHED, FINISHED_WATCHED, create_connect, settings
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

    finished_game_statistic = statistic_string(finished_games)
    finished_watched_game_statistic = statistic_string(finished_watched_games)

    total_price_finished_games = total_price(finished_games)
    total_price_finished_watched_games = total_price(finished_watched_games)

    headers = ['Название', 'Цена']

    return render_template_string('''\
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

        #form_error {
            color: red;
        }

        input[type="text"] {
            width: 100%;
        }

    </style>
</head>
<body>
    Последнее обновление было: {{ last_run_date }}
    <br><br>

    <table id="info_table">
        <tr>
            <td>Итого по пройденным играм:</td><td>{{ total_price_finished_games }}</td>
            <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>Пройденных игр:</td><td>{{finished_games|length}}</td>
        </tr>
        <tr>
            <td>Итого по просмотренным играм:</td><td>{{ total_price_finished_watched_games }}</td>
            <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>Просмотренных игр:</td><td>{{finished_watched_games|length}}</td>
        </tr>
        <tr>
            <td>Общая сумма:</td><td>{{ total_price_finished_games + total_price_finished_watched_games }}</td>
            <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
            <td>Всего игр:</td><td>{{finished_games|length + finished_watched_games|length}}</td>
        </tr>
    <table>
    <br>

    <div onsubmit="return checkForm(this)" id="top_right_fixed_panel">
        <form method="post" action="/set_price">
            <b>Установка цены у игры:</b>
            <p>Название:</p><p><input id="form_name" type="text" name="name"></p>
            <p>Цена:</p><p><input id="form_price" type="text" name="price"></p>
            <p><input type="submit" value="Установить цену"></p>
            <p id="form_error"></p>
        </form>

        <script type="text/javascript">
            function checkForm(form) {
                var form_error = document.getElementById('form_error');

                if (document.getElementById('form_name').value == ""
                        || document.getElementById('form_price').value == "") {
                    form_error.innerHTML = "Все поля нужно заполнять!";
                    return false;
                }
                form_error.innerHTML = "";

                return true;
            };
        </script>
    </div>

    <table id="finished_game" width="70%" border="1">
        <caption>Пройденные игры {{ finished_game_statistic }}</caption>
        <tr>
        {% for header in headers %}
            <th>{{ header }}</th>
        {% endfor %}
        </tr>

        {% for name, price in finished_games %}
            <tr><td>{{ name }}</td><td>{{ price }}</td></tr>
        {% endfor %}

        <tr><td align="right">Итого:</td><td>{{ total_price_finished_games }}</td></tr>
    </table>
    <br><br><br>

    <table id="finished_watched_game" width="70%" border="1">
        <caption>Просмотренные игры {{ finished_watched_game_statistic }}</caption>
        <tr>
        {% for header in headers %}
            <th>{{ header }}</th>
        {% endfor %}
        </tr>

        {% for name, price in finished_watched_games %}
            <tr><td>{{ name }}</td><td>{{ price }}</td></tr>
        {% endfor %}

        <tr><td align="right">Итого:</td><td>{{ total_price_finished_watched_games }}</td></tr>
    </table>

    <script>
        // Функция выделяет те игры, в которых еще не указана цена
        function fill_background_game_with_empty_price(table_id) {
            var rows = document.getElementById(table_id).rows;

            // Пропускаем первую строку, т.к. это заголовок
            for (var i = 1; i < rows.length; i++) {
                var name = rows[i].cells[0];
                var price = rows[i].cells[1];

                if (price.innerHTML == "None") {
                    name.className += " price_is_none";
                    price.className += " price_is_none";
                }
            }
        }

        fill_background_game_with_empty_price("finished_game");
        fill_background_game_with_empty_price("finished_watched_game");
    </script>
</body>
</html>
''',
        headers=headers,
        finished_games=finished_games, finished_watched_games=finished_watched_games,
        finished_game_statistic=finished_game_statistic,
        finished_watched_game_statistic=finished_watched_game_statistic,
        total_price_finished_games=total_price_finished_games,
        total_price_finished_watched_games=total_price_finished_watched_games,
        last_run_date=settings.last_run_date,
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
