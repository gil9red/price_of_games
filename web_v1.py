#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import config

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


from flask import Flask, render_template, request
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

# Добавление функции внутрь шаблона
app.jinja_env.globals.update(round_price=round_price)


@app.route("/")
def index():
    print('index')

    from common import FINISHED, FINISHED_WATCHED, create_connect, Settings, get_duplicates
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

        settings = Settings(connect=connect)
        last_run_date = settings.last_run_date

    finally:
        connect.close()

    return render_template(
        'index_v1.html',
        headers=['Название', 'Цена (руб.)'],
        finished_games=finished_games, finished_watched_games=finished_watched_games,
        finished_game_statistic=statistic_string(finished_games),
        finished_watched_game_statistic=statistic_string(finished_watched_games),
        total_price_finished_games=total_price(finished_games),
        total_price_finished_watched_games=total_price(finished_watched_games),
        last_run_date=last_run_date,
        has_duplicates=bool(get_duplicates()),
        UNKNOWN_PRICE_TITLE='Цена не задана',

        TEST_MODE=config.TEST_MODE,
        DB_FILE_NAME=config.DB_FILE_NAME,
        BACKUP_GIST=config.BACKUP_GIST,
        BACKUP_DIR_LIST=config.BACKUP_DIR_LIST,
    )


@app.route("/set_price", methods=['POST'])
def set_price():
    """
    Функция устанавливает цену для указанной игры.

    """

    print('set_price')

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

    print('rename_game')

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

    print('check_price')

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

    print('check_price_all_non_price_games')

    from common import check_price_all_non_price_games
    check_price_all_non_price_games()

    from flask import redirect
    return redirect("/")


if __name__ == '__main__':
    # Localhost
    app.debug = True

    app.run(
        port=5000,

        # Включение поддержки множества подключений
        threaded=True,
    )

    # # Public IP
    # app.run(host='0.0.0.0')
