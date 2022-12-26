#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import re
import os.path
import sys
from pathlib import Path

# Папка выше
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app_web.app import app, log
from flask import render_template, request, jsonify, send_from_directory

import config
from db import Settings
from common import WebUserAlertException, FINISHED_GAME, FINISHED_WATCHED
from app_parser import logic
from app_parser.main import run as run_check_of_price


@app.route("/")
def index():
    log.debug('Call index')

    return render_template(
        'index.html',
        last_run_date=Settings.get_value('last_run_date'),
        DB_FILE_NAME=config.DB_FILE_NAME,
        BACKUP_DIR_LIST=list(map(str, config.BACKUP_DIR_LIST)),

        FINISHED_GAME=FINISHED_GAME,
        FINISHED_WATCHED=FINISHED_WATCHED,

        TITLE_FINISHED_GAME='Пройденные игры',
        TITLE_FINISHED_WATCHED='Просмотренные игры',
    )


@app.route("/set_price", methods=['POST'])
def set_price():
    """
    Функция устанавливает цену для указанной игры.

    """

    log.debug('Call set_price')
    log.debug('request.form: %s', request.form)

    try:
        if 'name' not in request.form or 'price' not in request.form:
            text = 'В запросе должны присутствовать параметры "name" и "price"'
            raise WebUserAlertException(text)

        name = request.form['name'].strip()
        price = request.form['price'].strip()
        price = re.sub(r'[^\d.,]', '', price)
        price = int(float(price))

        log.debug(f'name={name!r} price={price!r}')

        if not logic.has_game(name):
            text = f'Игры с названием {name!r} не существует'
            raise WebUserAlertException(text)

        old_price = logic.get_price(name)
        if old_price is None:
            old_price = '<не задана>'

        if old_price == price:
            text = f'У игры {name!r} уже такая цена!'
            raise WebUserAlertException(text)

        # В modify_id_games будет список игр с названием <name>
        modify_id_games = logic.set_price_game(name, price)

        status = 'ok'
        text = f'Игре {name!r} установлена цена {price!r} (предыдущая цена: {old_price!r})'
        result = {
            'new_price': price,
            'modify_id_games': modify_id_games,
        }

    except WebUserAlertException as e:
        status = 'warning'
        text = str(e)
        result = None

    data = {
        'status': status,
        'text': text,
        'result': result,
    }
    log.debug(data)

    return jsonify(data)


@app.route("/rename_game", methods=['POST'])
def rename_game():
    """
    Функция изменяет название игры.
    Используется после изменения названия игры в гистах.

    """

    log.debug('Call rename_game')
    log.debug('request.form: %s', request.form)
    log.debug('request.args: %s', request.args)

    try:
        if 'old_name' not in request.form or 'new_name' not in request.form:
            text = 'В запросе должны присутствовать параметры "old_name" и "new_name"'
            raise WebUserAlertException(text)

        old_name = request.form['old_name'].strip()
        new_name = request.form['new_name'].strip()
        log.debug(f'old_name={old_name!r}, new_name={new_name!r}')

        status = 'ok'
        text = f'Игра {old_name!r} переименована в {new_name!r}'

        if old_name == new_name:
            text = f'У игры {old_name!r} уже такое название!'
            raise WebUserAlertException(text)

        result_rename = logic.rename_game(old_name, new_name)

        # Возможно, после переименования игры мы смогли найти ее цену...
        price = result_rename['price']
        if price:
            text += f' и найдена ее цена: {price!r}'

        # Просто без напряга возвращаем весь список и на странице заменяем все игры
        result = {
            logic.FINISHED_GAME:    logic.get_finished_games(),
            logic.FINISHED_WATCHED: logic.get_finished_watched_games(),
        }

    except WebUserAlertException as e:
        status = 'warning'
        text = str(e)
        result = None

    data = {
        'status': status,
        'text': text,
        'result': result,
    }
    # log.debug(data)

    return jsonify(data)


@app.route("/check_price", methods=['POST'])
def check_price():
    """
    Функция запускает проверку цены у указанной игры.

    """

    log.debug('Call check_price')
    log.debug('request.form: %s', request.form)

    try:
        if 'name' not in request.form:
            text = 'В запросе должен присутствовать параметр "name"'
            raise WebUserAlertException(text)

        name = request.form['name'].strip()
        log.debug(name)

        id_games_with_changed_price, price = logic.check_and_fill_price_of_game(name, cache=False)

        if price is None:
            status = 'ok'
            text = f'Не получилось найти цену для игры {name!r}'
            result = None

        else:
            status = 'ok'
            text = f'Для игры {name!r} найдена и установлена цена: {price!r}'
            result = {
                'new_price': price,
                'id_games_with_changed_price': id_games_with_changed_price,
            }

    except WebUserAlertException as e:
        status = 'warning'
        text = str(e)
        result = None

    data = {
        'status': status,
        'text': text,
        'result': result,
    }
    log.debug(data)

    return jsonify(data)


@app.route("/run_check", methods=['POST'])
def run_check():
    """
    Функция запускает проверку новых игр у парсера в main.py
    """

    log.debug('Call run_check')

    status = 'ok'
    result = None
    added_data = None
    text = '<b>Проверка новых игр завершена.</b>'

    try:
        added_finished_games, added_watched_games = run_check_of_price()
        if added_finished_games or added_watched_games:
            text += f'''
                <br>
                <table border="0">
                    <tr>
                        <td>Добавлено пройденных игр:</td>
                        <td align="right" style="width: 20px">{added_finished_games}</td>
                    </tr>
                    <tr>
                        <td>Добавлено просмотренных игр:</td>
                        <td align="right" style="width: 20px">{added_watched_games}</td>
                    </tr>
                </table>
            '''
            added_data = dict(
                added_finished_games=added_finished_games,
                added_watched_games=added_watched_games
            )
        else:
            text += '<br>Новый игр нет'

    except Exception as e:
        status = 'warning'
        text = f'<b>Проверка новых игр завершена ошибкой: "{e}".</b>'

    data = {
        'status': status,
        'text': text,
        'result': result,
        'data': added_data,
    }
    log.debug(data)

    return jsonify(data)


@app.route("/check_price_all_non_price_games")
def check_price_all_non_price_games():
    """
    Функция принудительной проверки цен всех игр для которых не получилось найти цену.

    """

    log.debug('Call check_price_all_non_price_games')

    try:
        games_with_changed_price = logic.check_price_all_non_price_games()
        log.debug(games_with_changed_price)

        status = 'ok'

        if games_with_changed_price:
            text = f'Цена найдена для {len(games_with_changed_price)} игр'

            # NOTE: если будет много игр, все не влезут
            # text = 'Цена найдена для {} игр:<br>'.format(len(games_with_changed_price))
            # for _, name, price in games_with_changed_price:
            #     text += '&nbsp;&nbsp;"{}" -> {}<br>'.format(name, price)

        else:
            text = 'Не удалось найти цену для игр'

        text = text.strip('<br>')

        result = {
            'games_with_changed_price': games_with_changed_price,
        }

    except WebUserAlertException as e:
        status = 'warning'
        text = str(e)
        result = None

    data = {
        'status': status,
        'text': text,
        'result': result,
    }
    log.debug(data)

    return jsonify(data)


@app.route("/get_games")
def get_games():
    """
    Функция для возврата всех игр в json.

    """

    log.debug('Call get_games')

    finished_games = logic.get_finished_games()
    finished_watched_games = logic.get_finished_watched_games()

    data = {
        logic.FINISHED_GAME:    finished_games,
        logic.FINISHED_WATCHED: finished_watched_games,
    }
    log.debug(f'Finished games: {len(finished_games)}')
    log.debug(f'Watched games: {len(finished_watched_games)}')
    log.debug(f'Total games: {len(finished_games) + len(finished_watched_games)}')

    return jsonify(data)


@app.route("/get_finished_games")
def get_finished_games():
    """
    Функция для возврата списка пройденных игр как json.

    """

    log.debug('Call get_finished_games')

    data = logic.get_finished_games()
    log.debug(f'Finished games: {len(data)}')

    return jsonify(data)


@app.route("/get_finished_watched_games")
def get_finished_watched_games():
    """
    Функция для возврата списка просмотренных игр как json.

    """

    log.debug('Call get_finished_watched_games')

    data = logic.get_finished_watched_games()
    log.debug(f'Watched games: {len(data)}')

    return jsonify(data)


@app.route("/delete_game", methods=['POST'])
def delete_game():
    """
    Функция для удаления указанной игры.

    """

    log.debug('Call delete_game')
    log.debug('request.form: %s', request.form)

    if 'name' not in request.form or 'kind' not in request.form:
        status = 'warning'
        text = 'В запросе должен присутствовать параметр "name" / "kind"'
        result = None

    else:
        name = request.form['name'].strip()
        log.debug(name)

        kind = request.form['kind'].strip()
        log.debug(kind)

        try:
            id_game = logic.delete_game(name, kind)

            status = 'ok'
            text = f'Удалена игра #{id_game} {name!r} ({kind!r})'
            result = {
                'id_game': id_game,
            }

        except WebUserAlertException as e:
            status = 'warning'
            text = str(e)
            result = None

    data = {
        'status': status,
        'text': text,
        'result': result,
    }
    log.debug(data)

    return jsonify(data)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static/images'),
        'favicon.png'
    )


if __name__ == '__main__':
    # app.debug = True

    app.run(
        port=config.PORT_WEB
    )

    # # Public IP
    # app.run(host='0.0.0.0')
