#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


"""
Этот скрипт анализирует файл с списком игр, заполняет sqlite базу пройденными и просмотренными играми, ищет цену
этим играм и заполняет указывает их играм.

"""

# # Тестовый режим
# import os
# os.environ['TEST_MODE'] = 'True'


from common import create_connect, get_games_list, append_games_to_base, fill_price_of_games, Settings, db_create_backup

# Создание базы и таблицы
connect = create_connect()
cursor = connect.cursor()

settings = Settings(connect=connect)

cursor.execute('''
CREATE TABLE IF NOT EXISTS Game (
    id INTEGER PRIMARY KEY,

    name TEXT NOT NULL,
    price TEXT DEFAULT NULL,
    modify_date TIMESTAMP DEFAULT NULL,
    kind TEXT NOT NULL,
    check_steam BOOLEAN NOT NULL DEFAULT 0
);
''')

connect.commit()

# NOTE: когда нужно в таблице подправить схему:
# cursor.executescript('''
# DROP TABLE Game2;
#
# CREATE TABLE IF NOT EXISTS Game2 (
#     id INTEGER PRIMARY KEY,
#
#     name TEXT NOT NULL,
#     price TEXT DEFAULT NULL,
#     modify_date TIMESTAMP DEFAULT NULL,
#     kind TEXT NOT NULL,
#     check_steam BOOLEAN NOT NULL DEFAULT 0
# );
#
# INSERT INTO Game2 SELECT * FROM Game;
#
# DROP TABLE Game;
# ALTER TABLE Game2 RENAME TO Game;
#
# ''')
#
# connect.commit()


def get_logger(name, file='log.txt', encoding='utf-8'):
    import logging
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] %(filename)s:%(lineno)d %(levelname)-8s %(message)s')

    from logging.handlers import RotatingFileHandler
    fh = RotatingFileHandler(file, maxBytes=10000000, backupCount=5, encoding=encoding)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    import sys
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(formatter)
    log.addHandler(sh)

    return log


log = get_logger('main__price_of_games', file='main.log')


def wait(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
    from datetime import timedelta, datetime
    today = datetime.today()
    timeout_date = today + timedelta(
        days=days, seconds=seconds, microseconds=microseconds,
        milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks
    )

    while today <= timeout_date:
        def str_timedelta(td):
            # Remove ms
            td = str(td)
            if '.' in td:
                td = td[:td.index('.')]

            return td

        left = timeout_date - today
        left = str_timedelta(left)

        print('\r' * 100, end='')
        print('До следующего запуска осталось {}'.format(left), end='')

        import sys
        sys.stdout.flush()

        # Delay 1 seconds
        import time
        time.sleep(1)

        today = datetime.today()

    print('\r' * 100, end='')
    print('\n')


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
        append_games_to_base(connect, finished_game_list, finished_watched_game_list)

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
