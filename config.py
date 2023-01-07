#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from pathlib import Path


DIR = Path(__file__).resolve().parent

DIR_LOG = DIR / 'logs'
DIR_LOG.mkdir(parents=True, exist_ok=True)

DB_DIR_NAME = DIR / 'database'
DB_DIR_NAME.mkdir(parents=True, exist_ok=True)

DB_FILE_NAME = str(DB_DIR_NAME / 'games.sqlite')

BACKUP_DIR_LIST = [
    DIR / 'backup',
    Path(r'C:\Users\ipetrash\Dropbox\backup_price_of_games'),
]

PORT_WEB = 5500
