#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


"""
Этот скрипт анализирует файл с списком игр, заполняет sqlite базу пройденными и просмотренными играми, 
ищет и заполняет цену.

"""


import datetime as DT
import json
import time
import sys

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from pathlib import Path

# Папка выше
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import PORT_RUN_CHECK
from common import get_logger

from db import Settings, db_create_backup
from third_party.wait import wait
from app_parser.utils import get_games_list
from app_parser.logic import append_games_to_database, fill_price_of_games


log = get_logger('main')


def run() -> tuple[int, int]:
    # Перед выполнением, запоминаем дату и время, чтобы иметь потом представление когда
    # в последний раз выполнялось заполнение списка
    Settings.set_value('last_run_date', DT.datetime.now())

    # Получение игр из файла gist
    finished_game_list, finished_watched_game_list = get_games_list()
    log.debug(
        "Пройденных игр %s, просмотренных игр: %s",
        len(finished_game_list),
        len(finished_watched_game_list)
    )

    # Добавление в базу новых игр
    added_finished_games, added_watched_games = append_games_to_database(
        finished_game_list, finished_watched_game_list
    )
    if added_finished_games:
        log.debug('Добавлено пройденных игр: %s', added_finished_games)

    if added_watched_games:
        log.debug('Добавлено просмотренных игр: %s', added_watched_games)

    # Заполнение цен игр
    fill_price_of_games()

    # Создание дубликата базы
    db_create_backup(log)

    return added_finished_games, added_watched_games


def _async_run_server(port):
    class HttpProcessor(BaseHTTPRequestHandler):
        def do_POST(self):
            code = 200

            log.debug("Серверный запуск проверки игр")
            try:
                added_finished_games, added_watched_games = run()
                data = {
                    'added_finished_games': added_finished_games,
                    'added_watched_games': added_watched_games,
                }
                data = json.dumps(data).encode('utf-8')

            except Exception as e:
                log.exception('Ошибка сервера:')
                code = 500
                data = f"{e}".encode('utf-8')

            self.send_response(code)
            self.send_header('Content-type', 'text/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(data)

    def _run_server(port: int):
        log.debug(f'HTTP server running on http://127.0.0.1:{port}')
        server_address = ('', port)
        httpd = HTTPServer(server_address, HttpProcessor)
        httpd.serve_forever()

    thread = Thread(target=_run_server, args=[port])
    thread.start()


if __name__ == '__main__':
    _async_run_server(port=PORT_RUN_CHECK)

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
            time.sleep(5 * 60)
