#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# Чтобы установить тестовый режим нужно будет в переменную TEST_MODE хотя бы что-то
# поместить и вызывать перед импортом модуля config
#
# Например:
# import os
# os.environ['TEST_MODE'] = 'True'
#
# import config
# import common


import os
TEST_MODE = bool(os.environ.get('TEST_MODE', ''))

# TEST_MODE = False
print('TEST_MODE:', TEST_MODE)

if TEST_MODE:
    DB_FILE_NAME = 'test_games.sqlite'
    BACKUP_GIST = False
    LOG_COMMON = 'test__common.log'
    LOG_APPEND_GAME = 'test__append_game.log'
    LOG_FILENAME = 'test__web.log'

else:
    DB_FILE_NAME = 'games.sqlite'
    BACKUP_GIST = True
    LOG_COMMON = 'common.log'
    LOG_APPEND_GAME = 'append_game.log'
    LOG_FILENAME = 'web.log'


BACKUP_DIR_LIST = [
    'backup',
    r'C:\Users\ipetrash\Dropbox\backup_price_of_games',
]

print('DB_FILE_NAME:', DB_FILE_NAME)
print('BACKUP_GIST:', BACKUP_GIST)
if BACKUP_GIST:
    print('BACKUP_DIR_LIST:', BACKUP_DIR_LIST)

print()
