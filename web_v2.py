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

    from common import create_connect, Settings, get_duplicates, get_finished_games, get_finished_watched_games

    finished_games = get_finished_games()
    finished_watched_games = get_finished_watched_games()

    connect = create_connect()

    try:
        settings = Settings(connect=connect)
        last_run_date = settings.last_run_date

    finally:
        connect.close()

    return render_template(
        'index_v2.html',
        last_run_date=last_run_date,
        has_duplicates=bool(get_duplicates()),

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

    try:
        if 'name' not in request.form or 'price' not in request.form:
            status = 'warning'
            text = 'В запросе должны присутствовать параметры "name" и "price"'
            result = None

        else:
            name = request.form['name']
            price = request.form['price']
            print(name, price)

            from common import set_price_game
            modify_id_games = set_price_game(name, price)

            if modify_id_games:
                status = 'ok'
                text = 'Игре "{}" установлена цена "{}"'.format(name, price)
                result = {
                    'new_price': price,
                    'modify_id_games': modify_id_games,
                }

            else:
                status = 'warning'
                text = 'Игры с названием "{}" не существует'.format(name)
                result = None

    except common.WebUserAlertException as e:
        status = 'warning'
        text = str(e)
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
    print(request.form)
    print(request.args)

    try:
        if 'old_name' not in request.form or 'new_name' not in request.form:
            status = 'warning'
            text = 'В запросе должны присутствовать параметры "old_name" и "new_name"'
            result = None

        else:
            old_name = request.form['old_name']
            new_name = request.form['new_name']
            print(old_name, new_name)

            from common import rename_game
            modify_id_games = rename_game(old_name, new_name)

            if modify_id_games:
                status = 'ok'
                text = 'Игра "{}" переименована в "{}"'.format(old_name, new_name)

                # Просто без напряга возвращаем весь список и на странице заменяем все игры
                from common import FINISHED, FINISHED_WATCHED, get_finished_games, get_finished_watched_games
                result = {
                    FINISHED: get_finished_games(),
                    FINISHED_WATCHED: get_finished_watched_games(),
                }

                # result = {
                #     'new_name': new_name,
                #     # 'new_price': new_price,
                #     'modify_id_games': modify_id_games,
                # }

            else:
                status = 'warning'
                text = 'Игры с названием "{0}" не существует'.format(new_name)
                result = None

    except common.WebUserAlertException as e:
        status = 'warning'
        text = str(e)
        result = None

    data = {
        'status': status,
        'text': text,
        'result': result,
    }
    print(data)

    from flask import jsonify
    return jsonify(data)


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


@app.route("/get_games")
def get_games():
    """
    Функция для возврата всех игр в json.

    """

    print('get_games')

    from common import FINISHED, FINISHED_WATCHED, get_finished_games, get_finished_watched_games
    data = {
        FINISHED: get_finished_games(),
        FINISHED_WATCHED: get_finished_watched_games(),
    }
    print(data)

    from flask import jsonify
    return jsonify(data)


# @app.route("/get_finished_games")
# def get_finished_games():
#     """
#     Функция для возврата списка пройденных игр как json.
#
#     """
#
#     print('get_finished_games')
#
#     from common import get_finished_games
#     data = get_finished_games()
#     print(data)
#
#     from flask import jsonify
#     return jsonify(data)
#
#
# @app.route("/get_finished_watched_games")
# def get_finished_watched_games():
#     """
#     Функция для возврата списка просмотренных игр как json.
#
#     """
#
#     print('get_finished_watched_games')
#
#     from common import get_finished_watched_games
#     data = get_finished_watched_games()
#     print(data)
#
#     from flask import jsonify
#     return jsonify(data)


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
