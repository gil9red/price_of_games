#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import json
import re
import os.path

from enum import Enum

from flask import render_template, request, jsonify, send_from_directory

import config

from app_parser import logic
from app_parser import models
from app_parser.main import run as run_check_of_price
from app_web.app import app, log
from common import WebUserAlertException, FINISHED_GAME, FINISHED_WATCHED
from db import Game, Genre, Settings
from integrator_genres.main import fill_from_current_games as run_check_of_genres


class StatusEnum(str, Enum):
    OK = "ok"
    WARNING = "warning"


def check_form_params(form: dict, *args):
    for arg in args:
        if arg not in form:
            text = f'В запросе отсутствует параметр "{arg}"'
            raise WebUserAlertException(text)


KIND_BY_TITLE: dict[str, str] = {
    FINISHED_GAME: "Пройденные игры",
    FINISHED_WATCHED: "Просмотренные игры",
}


def prepare_response(
    status: StatusEnum,
    text: str,
    result: None | list[models.GameInfo]
) -> dict:
    return {
        "status": status,
        "text": text,
        "result": result,
    }


@app.route("/")
def index():
    log.debug("Call index")

    return render_template(
        "index.html",

        # Parameters to template
        last_run_date=Settings.get_value("last_run_date"),
        db_file_name=config.DB_FILE_NAME,
        backup_dir_list=list(map(str, config.BACKUP_DIR_LIST)),
        title_games="Завершенные игры",
        finished_game=FINISHED_GAME,
        finished_watched=FINISHED_WATCHED,
        kind_by_title=KIND_BY_TITLE,
        kind_by_emoji={
            FINISHED_GAME: "🎮",
            FINISHED_WATCHED: "📺",
        },
        all_genres={
            genre.name: {
                "description": genre.description,
                "aliases": genre.aliases,
            }
            for genre in Genre.select()
        },
    )


@app.route("/api/set_price", methods=["POST"])
def set_price():
    """
    Функция устанавливает цену для указанной игры.

    """

    log.debug("Call set_price")
    log.debug("request.form: %s", request.form)

    try:
        check_form_params(request.form, "name", "price")

        name = request.form["name"].strip()
        price = request.form["price"].strip()
        price = re.sub(r"[^\d.,]", "", price).replace(",", ".")
        price = int(float(price))

        log.debug(f"name={name!r} price={price!r}")

        if not logic.has_game(name):
            text = f"Игры с названием {name!r} не существует"
            raise WebUserAlertException(text)

        old_price = logic.get_price(name)
        if old_price is None:
            old_price = "<не задана>"

        if old_price == price:
            text = f"У игры {name!r} уже такая цена!"
            raise WebUserAlertException(text)

        # В modify_id_games будет список игр с названием <name>
        modify_id_games = logic.set_price_game(name, price)

        status = StatusEnum.OK
        text = (
            f"Игре {name!r} установлена цена {price!r} (предыдущая цена: {old_price!r})"
        )
        result = logic.get_games_info(modify_id_games)

    except WebUserAlertException as e:
        status = StatusEnum.WARNING
        text = str(e)
        result = None

    data = prepare_response(
        status=status,
        text=text,
        result=result,
    )
    log.debug(data)

    return jsonify(data)


@app.route("/api/set_genres", methods=["POST"])
def set_genres():
    """
    Функция устанавливает жанры для указанной игры.

    """

    log.debug("Call set_genres")
    log.debug("request.form: %s", request.form)

    try:
        check_form_params(request.form, "name", "genres")

        name = request.form["name"].strip()
        genres = json.loads(request.form["genres"])

        log.debug(f"name={name!r} genres={genres!r}")

        if not logic.has_game(name):
            text = f"Игры с названием {name!r} не существует"
            raise WebUserAlertException(text)

        # В modify_id_games будет список игр с названием <name>
        modify_id_games = logic.set_genres(name, genres)

        status = StatusEnum.OK
        text = f"В игре {name!r} успешно изменен список жанров"
        result = logic.get_games_info(modify_id_games)

    except WebUserAlertException as e:
        status = StatusEnum.WARNING
        text = str(e)
        result = None

    data = prepare_response(
        status=status,
        text=text,
        result=result,
    )
    log.debug(data)

    return jsonify(data)


@app.route("/api/rename_game", methods=["POST"])
def rename_game():
    """
    Функция изменяет название игры.
    Используется после изменения названия игры в гистах.

    """

    log.debug("Call rename_game")
    log.debug("request.form: %s", request.form)

    try:
        check_form_params(request.form, "id", "new_name")

        game_id = int(request.form["id"].strip())
        game = Game.get_by_id(game_id)
        log.debug(f"Действие будет выполнено над: {game}")

        old_name = game.name
        new_name = request.form["new_name"].strip()
        log.debug(f"old_name={old_name!r}, new_name={new_name!r}")

        status = StatusEnum.OK
        text = f"Игра {old_name!r} переименована в {new_name!r}"

        if old_name == new_name:
            text = f"У игры {old_name!r} уже такое название!"
            raise WebUserAlertException(text)

        # TODO: Использовать точечную замену имени (и поиска цены)
        result_rename = logic.rename_game(old_name, new_name)

        # Возможно, после переименования игры мы смогли найти ее цену...
        price = result_rename.price
        if price:
            text += f" и найдена ее цена: {price!r}"

        # NOTE: Формат подразумевает список
        # Указываем game_id, чтобы в функции перечитался объект из базы
        result = [logic.get_game_info(game=game_id)]

    except WebUserAlertException as e:
        status = StatusEnum.WARNING
        text = str(e)
        result = None

    data = prepare_response(
        status=status,
        text=text,
        result=result,
    )
    log.debug(data)

    return jsonify(data)


@app.route("/api/check_price", methods=["POST"])
def check_price():
    """
    Функция запускает проверку цены у указанной игры.

    """

    log.debug("Call check_price")
    log.debug("request.form: %s", request.form)

    try:
        check_form_params(request.form, "id")

        game_id = int(request.form["id"].strip())
        game = Game.get_by_id(game_id)
        log.debug(f"Действие будет выполнено над: {game}")

        name = game.name

        # TODO: Использовать точечный поиск цены
        price_update_result = logic.check_and_fill_price_of_game(name, cache=False)

        price = price_update_result.price
        if price is None:
            status = StatusEnum.OK
            text = f"Не получилось найти цену для игры {name!r}"
            result = None

        else:
            status = StatusEnum.OK
            text = f"Для игры {name!r} найдена и установлена цена: {price!r}"
            result = logic.get_games_info(price_update_result.game_ids)

    except WebUserAlertException as e:
        status = StatusEnum.WARNING
        text = str(e)
        result = None

    data = prepare_response(
        status=status,
        text=text,
        result=result,
    )
    log.debug(data)

    return jsonify(data)


@app.route("/api/run_check_prices", methods=["POST"])
def run_check_prices():
    """
    Функция запускает проверку новых игр у парсера в main.py
    """

    log.debug("Call run_check_prices")

    status = StatusEnum.OK
    result = None
    text = "<b>Проверка новых игр завершена.</b>"

    try:
        added_finished_game_ids, added_watched_game_ids = run_check_of_price()
        if added_finished_game_ids or added_watched_game_ids:
            text += f"""
                <br>
                <table border="0">
                    <tr>
                        <td>Добавлено пройденных игр:</td>
                        <td align="right" style="width: 20px">{len(added_finished_game_ids)}</td>
                    </tr>
                    <tr>
                        <td>Добавлено просмотренных игр:</td>
                        <td align="right" style="width: 20px">{len(added_watched_game_ids)}</td>
                    </tr>
                </table>
            """
            result = logic.get_games_info(
                added_finished_game_ids + added_watched_game_ids
            )
        else:
            text += "<br>Новых игр нет"

    except Exception as e:
        status = StatusEnum.WARNING
        text = f'<b>Проверка новых игр завершена ошибкой: "{e}".</b>'
        log.exception("Проверка новых игр завершена ошибкой:")

    data = prepare_response(
        status=status,
        text=text,
        result=result,
    )
    log.debug(data)

    return jsonify(data)


@app.route("/api/run_check_genres", methods=["POST"])
def run_check_genres():
    """
    Функция запускает проверку новых жанров у игр без жанров
    """

    log.debug("Call run_check_genres")

    status = StatusEnum.OK
    result = None
    text = "<b>Проверка заполнения жанров играм завершена.</b>"

    try:
        if ids := run_check_of_genres():
            text += f"<br>Обновлено игр: {len(ids)}"
            result = logic.get_games_info(ids)
        else:
            text += "<br>Без изменений"

    except Exception as e:
        status = StatusEnum.WARNING
        text = f'<b>Проверка новых жанров у игр завершена ошибкой: "{e}".</b>'
        log.exception("Проверка новых жанров у игр завершена ошибкой:")

    data = prepare_response(
        status=status,
        text=text,
        result=result,
    )
    log.debug(data)

    return jsonify(data)


@app.route("/api/check_price_all_non_price_games")
def check_price_all_non_price_games():
    """
    Функция принудительной проверки цен всех игр для которых не получилось найти цену.

    """

    log.debug("Call check_price_all_non_price_games")

    try:
        game_ids: list[int] = []
        for result in logic.check_price_all_non_price_games():
            for game_id in result.game_ids:
                if game_id not in game_ids:
                    game_ids.append(game_id)

        log.debug(game_ids)

        status = StatusEnum.OK

        if game_ids:
            text = f"Цена найдена для {len(game_ids)} игр"
        else:
            text = "Не удалось найти цену для игр"

        text = text.strip("<br>")

        result = logic.get_games_info(game_ids)

    except WebUserAlertException as e:
        status = StatusEnum.WARNING
        text = str(e)
        result = None

    data = prepare_response(
        status=status,
        text=text,
        result=result,
    )
    log.debug(data)

    return jsonify(data)


@app.route("/api/get_games")
def get_games():
    """
    Функция для возврата всех игр в json.

    """

    log.debug("Call get_games")

    data = logic.get_games()
    log.debug(f"Total games: {len(data)}")

    return jsonify(data)


@app.route("/api/search/<text>")
def get_api_search(text: str):
    """
    Функция для возврата списка игр по названию.

    """

    log.debug("Call get_api_search")

    items = logic.search(text)
    log.debug(f"Found: {len(items)}")

    return jsonify(items)


@app.route("/api/delete_game", methods=["POST"])
def delete_game():
    """
    Функция для удаления указанной игры.

    """

    log.debug("Call delete_game")
    log.debug("request.form: %s", request.form)

    try:
        check_form_params(request.form, "id")

        game_id = int(request.form["id"].strip())
        game = Game.get_by_id(game_id)
        log.debug(f"Действие будет выполнено над: {game}")

        # NOTE: Формат подразумевает список
        result = [logic.get_game_info(game)]

        logic.delete_game(game)

        status = StatusEnum.OK
        text = f"Удалена игра #{game_id} {game.name!r} ({game.platform.name!r}, {KIND_BY_TITLE[game.kind]!r})"

    except WebUserAlertException as e:
        status = StatusEnum.WARNING
        text = str(e)
        result = None

    data = prepare_response(
        status=status,
        text=text,
        result=result,
    )
    log.debug(data)

    return jsonify(data)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static/images"), "favicon.png"
    )


if __name__ == "__main__":
    # app.debug = True

    app.run(port=config.PORT_WEB)

    # # Public IP
    # app.run(host='0.0.0.0')
