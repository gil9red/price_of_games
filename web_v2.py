#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# Установка тестового режима, нужно вызывать перед импортом модуля config
import os
os.environ['TEST_MODE'] = 'True'

import config


import common


# TODO: окну фильтра добавить кнопку очищения его


from flask import Flask, render_template, request
app = Flask(__name__)

import logging
logging.basicConfig(level=logging.DEBUG)


@app.route("/")
def index():
    print('index')

    from common import FINISHED, FINISHED_WATCHED, create_connect, Settings, get_duplicates
    connect = create_connect()

    try:
        cursor = connect.cursor()

        get_game_sql = '''
            SELECT id, name, price
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
        'index_v2.html',
        headers=['Название', 'Цена (руб.)'],
        finished_games=finished_games, finished_watched_games=finished_watched_games,
        last_run_date=last_run_date,
        has_duplicates=bool(get_duplicates()),
        UNKNOWN_PRICE_TITLE='Цена не задана',

        TEST_MODE=config.TEST_MODE,
        DB_FILE_NAME=common.DB_FILE_NAME,
        BACKUP_GIST=common.BACKUP_GIST,
        BACKUP_DIR_LIST=common.BACKUP_DIR_LIST,
    )


@app.route("/set_price", methods=['POST'])
def set_price():
    """
    Функция устанавливает цену для указанной игры.

    """

    print('set_price')
    print(request.form)

    name = request.form['name']
    price = request.form['price']
    print(name, price)

    from common import set_price_game
    modify_id_games = set_price_game(name, price)

    if modify_id_games:
        status = 'ok'
        text = 'Игре "{0}" удачно установлена цена "{1}"'.format(name, price)
        result = {
            'new_price': price,
            'modify_id_games': modify_id_games,
        }

    else:
        status = 'warning'
        text = 'Игры с названием "{0}" не существует'.format(name)
        result = None

    data = {
        'status': status,
        'text': text,
        'result': result,
    }
    print(data)

    from flask import jsonify
    return jsonify(data)


@app.route("/rename_game", methods=['POST'])
def rename_game():
    """
    Функция изменяет название игры.
    Используется после изменения названия игры в гистах.

    """

    print('rename_game')

    if request.method == 'POST':
        print(request.form)
        print(request.args)

        # if 'old_name' in request.form and 'new_name' in request.form:
        #     old_name = request.form['old_name']
        #     new_name = request.form['new_name']
        #     print(old_name, new_name)
        #
        #     from common import rename_game
        #     rename_game(old_name, new_name)

    from flask import redirect
    return redirect("/")


@app.route("/check_price", methods=['POST'])
def check_price():
    """
    Функция запускает проверку цены у указанной игры.

    """

    print('check_price')

    # if request.method == 'POST':
    #     print(request.form)
    #
    #     if 'name' in request.form:
    #         name = request.form['name']
    #         print(name)
    #
    #         from common import check_and_fill_price_of_game
    #         check_and_fill_price_of_game(name)

    from flask import redirect
    return redirect("/")


@app.route("/check_price_all_non_price_games")
def check_price_all_non_price_games():
    """
    Функция принудительной проверки цен всех игр для которых не получилось найти цену.

    """

    print('check_price_all_non_price_games')
    # print(request.form)
    # print(request.args)

    # from common import check_price_all_non_price_games
    # check_price_all_non_price_games()

    # from flask import redirect
    # return redirect("/")

    data = {
        'status': 'ok',
    }

    from flask import jsonify
    return jsonify(data)


if __name__ == '__main__':
    # Localhost
    app.debug = True

    app.run(
        port=5500,

        # Включение поддержки множества подключений
        threaded=True,
    )

    # # Public IP
    # app.run(host='0.0.0.0')
