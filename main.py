#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


"""
Этот скрипт анализирует файл с списком игр, заполняет sqlite базу пройденными и просмотренными играми, ищет цену
этим играм и заполняет указывает их играм.

"""


from common import create_connect, get_games_list, append_games_to_base, fill_price_of_games, settings, db_create_backup

# Создание базы и таблицы
connect = create_connect()
cursor = connect.cursor()

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


while True:
    # Перед выполнением, запоминаем дату и время, чтобы иметь потом представление когда
    # в последний раз выполнялось заполнение списка
    from datetime import datetime
    settings.last_run_date = datetime.today()

    finished_game_list, finished_watched_game_list = get_games_list()
    print("Пройденных игр {}, просмотренных игр: {}".format(len(finished_game_list), len(finished_watched_game_list)))

    # Добавление в базу новых игр
    append_games_to_base(connect, finished_game_list, finished_watched_game_list)

    # Заполнение цен игр
    fill_price_of_games(connect)

    # Создание дубликата базы
    db_create_backup()

    # Every 1 days
    from datetime import timedelta
    today = datetime.today()
    timeout_date = today + timedelta(days=1)

    while today <= timeout_date:
        print('\r' * 50, end='')
        print('До следующего запуска осталось {}'.format(timeout_date - today), end='')

        import sys
        sys.stdout.flush()

        # Delay 1 seconds
        import time
        time.sleep(1)

        today = datetime.today()

    print('\r' * 50, end='')
    print('\n')
