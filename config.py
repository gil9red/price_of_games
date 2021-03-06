#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from pathlib import Path


DIR = Path(__file__).resolve().parent

DIR_LOG = DIR / 'logs'
DB_FILE_NAME = DIR / 'games.sqlite'


BACKUP_DIR_LIST = [
    DIR / 'backup',
    Path(r'C:\Users\ipetrash\Dropbox\backup_price_of_games'),
]


PORT_WEB = 5500
PORT_RUN_CHECK = 5501
