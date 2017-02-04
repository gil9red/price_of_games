#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# Чтобы установить тестовый режим нужно будет в переменную TEST_MODE хотя бы что-то
# поместить и вызывать перед импортом модуля config
import os
TEST_MODE = bool(os.environ.get('TEST_MODE', ''))

# TEST_MODE = False
print('TEST_MODE:', TEST_MODE)

if not TEST_MODE:
    DB_FILE_NAME = 'games.sqlite'
    BACKUP_GIST = True

else:
    DB_FILE_NAME = 'test_games.sqlite'
    BACKUP_GIST = False

BACKUP_DIR_LIST = [
    'backup',
    r'C:\Users\ipetrash\Dropbox\backup_price_of_games',
]

print('DB_FILE_NAME:', DB_FILE_NAME)
print('BACKUP_GIST:', BACKUP_GIST)
if BACKUP_GIST:
    print('BACKUP_DIR_LIST:', BACKUP_DIR_LIST)

print()
