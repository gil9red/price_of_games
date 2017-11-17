#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# # Тестовый режим
# import os
# os.environ['TEST_MODE'] = 'True'


import config
import common


# TODO: таблицы с статистикой и информацией для разработчика объединить в одну таблицу,
#       добавив таблицу с фильтрами и сортировкой
# TODO: возможность прятать таблицы (вывести в заголовок или footer самой страницы)
# TODO: обновить скриншот
# TODO: добавить возможность выполнить sql запрос
# TODO: нарисовать график указания цен на игры:
#     modify_date_list = connect.execute("SELECT modify_date "
#                                        "FROM Game "
#                                        "WHERE modify_date IS NOT NULL "
#                                        "ORDER BY modify_date").fetchall()
#     modify_date_list = [item for (item,) in modify_date_list]
#     print(modify_date_list)
#
# Ось X -- дата
# Ось Y -- количество игр в текущей дате


from app import app, logger
from flask import render_template, request


@app.route("/")
def index():
    logger.debug('index')

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

        FINISHED=common.FINISHED,
        FINISHED_WATCHED=common.FINISHED_WATCHED,
    )


@app.route("/set_price", methods=['POST'])
def set_price():
    """
    Функция устанавливает цену для указанной игры.

    """

    logger.debug('set_price')
    logger.debug(request.form)

    try:
        if 'name' not in request.form or 'price' not in request.form:
            status = 'warning'
            text = 'В запросе должны присутствовать параметры "name" и "price"'
            result = None

        else:
            name = request.form['name'].strip()
            price = request.form['price'].strip()
            logger.debug('%s %s', name, price)

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
    logger.debug(data)

    from flask import jsonify
    return jsonify(data)


@app.route("/rename_game", methods=['POST'])
def rename_game():
    """
    Функция изменяет название игры.
    Используется после изменения названия игры в гистах.

    """

    logger.debug('rename_game')
    logger.debug(request.form)
    logger.debug(request.args)

    try:
        if 'old_name' not in request.form or 'new_name' not in request.form:
            status = 'warning'
            text = 'В запросе должны присутствовать параметры "old_name" и "new_name"'
            result = None

        else:
            old_name = request.form['old_name'].strip()
            new_name = request.form['new_name'].strip()
            logger.debug('%s %s', old_name, new_name)

            status = 'ok'
            text = 'Игра "{}" переименована в "{}"'.format(old_name, new_name)

            from common import rename_game
            result_rename = rename_game(old_name, new_name)

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

    except common.WebUserAlertException as e:
        status = 'warning'
        text = str(e)
        result = None

    data = {
        'status': status,
        'text': text,
        'result': result,
    }
    logger.debug(data)

    from flask import jsonify
    return jsonify(data)


@app.route("/check_price", methods=['POST'])
def check_price():
    """
    Функция запускает проверку цены у указанной игры.

    """

    logger.debug('check_price')
    logger.debug(request.form)

    try:
        if 'name' not in request.form:
            status = 'warning'
            text = 'В запросе должен присутствовать параметр "name"'
            result = None

        else:
            name = request.form['name'].strip()
            logger.debug(name)

            from common import check_and_fill_price_of_game
            id_games_with_changed_price, price = check_and_fill_price_of_game(name, cache=False)

            if price is None:
                status = 'ok'
                text = 'Не получилось найти цену для игры "{}"'.format(name)
                result = None

            else:
                status = 'ok'
                text = 'Для игры "{}" найдена и установлена цена: "{}"'.format(name, price)
                result = {
                    'new_price': price,
                    'id_games_with_changed_price': id_games_with_changed_price,
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
    logger.debug(data)

    from flask import jsonify
    return jsonify(data)


@app.route("/check_price_all_non_price_games")
def check_price_all_non_price_games():
    """
    Функция принудительной проверки цен всех игр для которых не получилось найти цену.

    """

    logger.debug('check_price_all_non_price_games')

    try:
        from common import check_price_all_non_price_games
        games_with_changed_price = check_price_all_non_price_games()
        logger.debug(games_with_changed_price)

        status = 'ok'

        if games_with_changed_price:
            text = 'Цена найдена для {} игр'.format(len(games_with_changed_price))

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

    except common.WebUserAlertException as e:
        status = 'warning'
        text = str(e)
        result = None

    data = {
        'status': status,
        'text': text,
        'result': result,
    }
    logger.debug(data)

    from flask import jsonify
    return jsonify(data)


# # функция нужна только для тестирования
# @app.route("/set_null_price", methods=['POST'])
# def set_null_price():
#     """
#     Функция убирает у игры цену т.е. будет значение null.
#
#     """
#
#     logger.debug('set_null_price')
#     logger.debug(request.form)
#
#     try:
#         if 'name' not in request.form:
#             status = 'warning'
#             text = 'В запросе должен присутствовать параметр "name"'
#             result = None
#
#         else:
#             name = request.form['name']
#             logger.debug(name)
#
#             from common import create_connect, get_id_games_by_name
#             try:
#                 connect = create_connect()
#                 connect.execute("UPDATE Game SET price = ? WHERE name = ?", (None, name))
#                 connect.commit()
#
#                 status = 'ok'
#                 text = 'Для игры "{}" убрана цена'.format(name)
#                 result = {
#                     'id_games_with_changed_price': get_id_games_by_name(name),
#                 }
#
#             finally:
#                 connect.close()
#
#     except common.WebUserAlertException as e:
#         status = 'warning'
#         text = str(e)
#         result = None
#
#     data = {
#         'status': status,
#         'text': text,
#         'result': result,
#     }
#     logger.debug(data)
#
#     from flask import jsonify
#     return jsonify(data)


@app.route("/get_games")
def get_games():
    """
    Функция для возврата всех игр в json.

    """

    logger.debug('get_games')

    from common import FINISHED, FINISHED_WATCHED, get_finished_games, get_finished_watched_games
    data = {
        FINISHED: get_finished_games(),
        FINISHED_WATCHED: get_finished_watched_games(),
    }
    logger.debug('Finished games: {}'.format(len(data[FINISHED])))
    logger.debug('Watched games: {}'.format(len(data[FINISHED_WATCHED])))
    logger.debug('Total games: {}'.format(len(data[FINISHED]) + len(data[FINISHED_WATCHED])))

    from flask import jsonify
    return jsonify(data)


@app.route("/get_finished_games")
def get_finished_games():
    """
    Функция для возврата списка пройденных игр как json.

    """

    logger.debug('get_finished_games')

    from common import get_finished_games
    data = get_finished_games()
    logger.debug('Finished games: {}'.format(len(data)))

    from flask import jsonify
    return jsonify(data)


@app.route("/get_finished_watched_games")
def get_finished_watched_games():
    """
    Функция для возврата списка просмотренных игр как json.

    """

    logger.debug('get_finished_watched_games')

    from common import get_finished_watched_games
    data = get_finished_watched_games()
    logger.debug('Watched games: {}'.format(len(data)))

    from flask import jsonify
    return jsonify(data)


@app.route("/delete_game", methods=['POST'])
def delete_game():
    """
    Функция для удаления указанной игры.

    """

    logger.debug('delete_game')
    logger.debug(request.form)

    if 'name' not in request.form or 'kind' not in request.form:
        status = 'warning'
        text = 'В запросе должен присутствовать параметр "name" / "kind"'
        result = None

    else:
        name = request.form['name'].strip()
        logger.debug(name)

        kind = request.form['kind'].strip()
        logger.debug(kind)

        try:
            from common import delete_game
            id_game = delete_game(name, kind)

            status = 'ok'
            text = 'Удалена игра #{} "{}" ({})'.format(id_game, name, kind)
            result = {
                'id_game': id_game,
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
    logger.debug(data)

    from flask import jsonify
    return jsonify(data)


if __name__ == '__main__':
    # # Localhost
    # app.debug = True

    app.run(
        port=5500,

        # Включение поддержки множества подключений
        threaded=True,
    )

    # # Public IP
    # app.run(host='0.0.0.0')
