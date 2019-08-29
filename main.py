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


from common import *

# Создание базы и таблицы
connect = create_connect()
cursor = connect.cursor()

settings = Settings(connect=connect)

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


while True:
    try:
        log.debug('Start')

        # Перед выполнением, запоминаем дату и время, чтобы иметь потом представление когда
        # в последний раз выполнялось заполнение списка
        from datetime import datetime
        settings.last_run_date = datetime.today()

        # Получение игр из файла gist
        finished_game_list, finished_watched_game_list = get_games_list()
        log.debug("Пройденных игр {}, просмотренных игр: {}".format(
            len(finished_game_list),
            len(finished_watched_game_list))
        )

        # Добавление в базу новых игр
        append_games_to_database(connect, finished_game_list, finished_watched_game_list)

        # Заполнение цен игр
        fill_price_of_games(connect)

        # Создание дубликата базы
        db_create_backup()

        # Every 1 days
        wait(days=1)

    except:
        log.exception('Ошибка:')
        log.debug('Через 5 минут попробую снова...')

        # Wait 5 minutes before next attempt
        import time
        time.sleep(5 * 60)
