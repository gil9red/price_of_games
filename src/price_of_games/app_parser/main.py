#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


"""
Этот скрипт анализирует файл с списком игр, заполняет sqlite базу пройденными и просмотренными играми, 
ищет и заполняет цену.

"""


import time
import sys
from datetime import datetime

from price_of_games.app_parser import log
from price_of_games.app_parser.utils import Game, get_games
from price_of_games.app_parser.logic import (
    append_games_to_database,
    fill_price_of_games,
)
from price_of_games.common import FINISHED_GAME, FINISHED_WATCHED
from price_of_games.db import Settings, db_create_backup
from price_of_games.integrity_check import run as run_integrity_check
from price_of_games.integrator_genres.main import run as fill_genres_of_games

# pip install simple-wait
from simple_wait import wait

IS_LOOP: bool = "--loop" in sys.argv


def run() -> tuple[list[int], list[int]]:
    log.debug("Start")

    # Перед выполнением, запоминаем дату и время, чтобы иметь потом представление когда
    # в последний раз выполнялось заполнение списка
    Settings.set_value("last_run_date", datetime.now())

    # Получение игр из файла gist
    finished_games: list[Game] = []
    finished_watched_games: list[Game] = []
    for game in get_games():
        if game.kind == FINISHED_GAME:
            finished_games.append(game)
        elif game.kind == FINISHED_WATCHED:
            finished_watched_games.append(game)

    log.debug(
        "Пройденных игр %s, просмотренных игр %s",
        len(finished_games),
        len(finished_watched_games),
    )

    # Добавление в базу новых игр
    added_finished_game_ids: list[int]
    added_watched_game_ids: list[int]
    added_finished_game_ids, added_watched_game_ids = append_games_to_database(
        finished_games, finished_watched_games
    )
    if added_finished_game_ids:
        log.debug("Добавлено пройденных игр: %s", added_finished_game_ids)

    if added_watched_game_ids:
        log.debug("Добавлено просмотренных игр: %s", added_watched_game_ids)

    # Заполнение цен игр
    fill_price_of_games()

    # Заполнение жанров игр
    fill_genres_of_games()

    # Проверка целостности
    run_integrity_check()

    # Создание бекапа базы
    if added_finished_game_ids or added_watched_game_ids:
        db_create_backup(log)

    return added_finished_game_ids, added_watched_game_ids


def run_loop() -> None:
    while True:
        try:
            run()

            # Every 1 hour
            wait(hours=1)

        except Exception:
            log.exception("Ошибка:")
            log.debug("Через 5 минут попробую снова...")

            # Wait 5 minutes before next attempt
            wait(minutes=5)


def main() -> None:
    if IS_LOOP:
        run_loop()
        return

    last_error: Exception | None = None
    for _ in range(5):
        try:
            run()
            return
        except Exception as e:
            last_error = e

            log.exception("Ошибка:")
            log.debug("Через 1 минуту попробую снова...")
            #  NOTE: Тут без wait, т.к. оно пишет в консоль обратный отсчет
            #        Что в некоторых случаях может быть неудобно
            time.sleep(60)

    raise last_error


if __name__ == "__main__":
    main()
