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

    from common import create_connect, Settings, get_duplicates
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
            result_rename = rename_game(old_name, new_name)
            if result_rename:
                status = 'ok'
                text = 'Игра "{}" переименована в "{}"'.format(old_name, new_name)

                # Возможно, после переименования игры мы смогли найти ее цену...
                price = result_rename['price']
                if price is not None:
                    text += ' и найдена ее цена: "{}"'.format(price)

                # Просто без напряга возвращаем весь список и на странице заменяем все игры
                from common import FINISHED, FINISHED_WATCHED, get_finished_games, get_finished_watched_games
                result = {
                    FINISHED: get_finished_games(),
                    FINISHED_WATCHED: get_finished_watched_games(),
                }

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
    print(request.form)

    try:
        if 'name' not in request.form:
            status = 'warning'
            text = 'В запросе должен присутствовать параметр "name"'
            result = None

        else:
            name = request.form['name']
            print(name)

            from common import check_and_fill_price_of_game
            id_games_with_changed_price, price = check_and_fill_price_of_game(name)

            if price is None:
                status = 'ok'
                text = 'Не получилось найти цену для игры "{}"'.format(name)
                result = {
                    'new_price': price,
                    'id_games_with_changed_price': id_games_with_changed_price,
                }

            else:
                status = 'ok'
                text = 'Для игры "{}" найдена и установлена цена: "{}"'.format(name, price)
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


@app.route("/check_price_all_non_price_games")
def check_price_all_non_price_games():
    """
    Функция принудительной проверки цен всех игр для которых не получилось найти цену.

    """

    print('check_price_all_non_price_games')

    try:
        from common import check_price_all_non_price_games
        games_with_changed_price = check_price_all_non_price_games()

        status = 'ok'

        if games_with_changed_price:
            text = 'Цена найдена для {} игр:\n'
            for name, price in games_with_changed_price:
                text += '  "{}" -> "{}"\n'.format(name, price)

        else:
            text = 'Не удалось найти цену для игр'

        text = text.strip()

        result = {
            'games_with_changed_price': games_with_changed_price,
        }

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


@app.route("/get_finished_games")
def get_finished_games():
    """
    Функция для возврата списка пройденных игр как json.

    """

    print('get_finished_games')

    from common import get_finished_games
    data = get_finished_games()
    print(data)

    from flask import jsonify
    return jsonify(data)


@app.route("/get_finished_watched_games")
def get_finished_watched_games():
    """
    Функция для возврата списка просмотренных игр как json.

    """

    print('get_finished_watched_games')

    from common import get_finished_watched_games
    data = get_finished_watched_games()
    print(data)

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
