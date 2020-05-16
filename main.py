#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


"""
Этот скрипт анализирует файл с списком игр, заполняет sqlite базу пройденными и просмотренными играми, 
ищет и заполняет цену.

"""

# # Тестовый режим
# import os
# os.environ['TEST_MODE'] = 'True'


import datetime as DT

from common import *
from config import PORT_RUN_CHECK


# Создание базы и таблицы
init_db()


log = get_logger('main__price_of_games', file='main.log')


def wait(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
    from datetime import timedelta, datetime
    from itertools import cycle
    import sys
    import time

    try:
        progress_bar = cycle('|/-\\|/-\\')

        today = datetime.today()
        timeout_date = today + timedelta(
            days=days, seconds=seconds, microseconds=microseconds,
            milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks
        )

        def str_timedelta(td: timedelta) -> str:
            td = str(td)

            # Remove ms
            # 0:01:40.123000 -> 0:01:40
            if '.' in td:
                td = td[:td.rindex('.')]

            # 0:01:40 -> 00:01:40
            if td.startswith('0:'):
                td = '00:' + td[2:]

            return td

        while today <= timeout_date:
            left = timeout_date - today
            left = str_timedelta(left)

            print('\r' + ' ' * 100 + '\r', end='')
            print('[{}] Time left to wait: {}'.format(next(progress_bar), left), end='')
            sys.stdout.flush()

            # Delay 1 seconds
            time.sleep(1)

            today = datetime.today()

        print('\r' + ' ' * 100 + '\r', end='')

    except KeyboardInterrupt:
        print()
        print('Waiting canceled')


def run() -> (int, int):
    with create_connect() as connect:
        # Перед выполнением, запоминаем дату и время, чтобы иметь потом представление когда
        # в последний раз выполнялось заполнение списка
        settings = Settings(connect)
        settings.last_run_date = DT.datetime.today()

        # Получение игр из файла gist
        finished_game_list, finished_watched_game_list = get_games_list()
        log.debug(
            "Пройденных игр %s, просмотренных игр: %s",
            len(finished_game_list),
            len(finished_watched_game_list)
        )

        # Добавление в базу новых игр
        added_finished_games, added_watched_games = append_games_to_database(
            connect, finished_game_list, finished_watched_game_list
        )
        if added_finished_games:
            log.debug('Добавлено пройденных игр: %s', added_finished_games)

        if added_watched_games:
            log.debug('Добавлено просмотренных игр: %s', added_watched_games)

        # Заполнение цен игр
        fill_price_of_games(connect)

    # Создание дубликата базы
    db_create_backup()

    return added_finished_games, added_watched_games


def _async_run_server(port):
    import json
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from threading import Thread

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
            except:
                log.exception('Ошибка сервера:')
                code = 500

            self.send_response(code)
            self.send_header('Content-type', 'text/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(
                json.dumps(data).encode('utf-8')
            )

    def _run_server(port):
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

            # Every 1 days
            wait(days=1)

        except:
            log.exception('Ошибка:')
            log.debug('Через 5 минут попробую снова...')

            # Wait 5 minutes before next attempt
            import time
            time.sleep(5 * 60)
