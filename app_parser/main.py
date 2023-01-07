#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


"""
Этот скрипт анализирует файл с списком игр, заполняет sqlite базу пройденными и просмотренными играми, 
ищет и заполняет цену.

"""


from datetime import datetime

from app_parser.utils import get_games
from app_parser.logic import append_games_to_database, fill_price_of_games
from common import get_logger, FINISHED_GAME, FINISHED_WATCHED
from db import Settings, db_create_backup
from third_party.wait import wait


log = get_logger('main')


def run() -> tuple[int, int]:
    # Перед выполнением, запоминаем дату и время, чтобы иметь потом представление когда
    # в последний раз выполнялось заполнение списка
    Settings.set_value('last_run_date', datetime.now())

    # Получение игр из файла gist
    games = get_games()
    finished_game_list = [
        game for game in games if game.kind == FINISHED_GAME
    ]
    finished_watched_game_list = [
        game for game in games if game.kind == FINISHED_WATCHED
    ]

    log.debug(
        "Пройденных игр %s, просмотренных игр: %s",
        len(finished_game_list),
        len(finished_watched_game_list)
    )

    # Добавление в базу новых игр
    added_finished_games, added_watched_games = append_games_to_database(
        finished_game_list,
        finished_watched_game_list
    )
    if added_finished_games:
        log.debug('Добавлено пройденных игр: %s', added_finished_games)

    if added_watched_games:
        log.debug('Добавлено просмотренных игр: %s', added_watched_games)

    # Заполнение цен игр
    fill_price_of_games()

    # Создание дубликата базы
    if added_finished_games or added_watched_games:
        db_create_backup(log)

    return added_finished_games, added_watched_games


if __name__ == '__main__':
    while True:
        try:
            log.debug('Start')

            run()

            # Every 1 hours
            wait(hours=1)

        except:
            log.exception('Ошибка:')
            log.debug('Через 5 минут попробую снова...')

            # Wait 5 minutes before next attempt
            wait(minutes=5)
