#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import os.path
from pathlib import Path


DIR = Path(__file__).resolve().parent

DIR_LOG = DIR / 'logs'
DIR_LOG.mkdir(parents=True, exist_ok=True)

DB_DIR_NAME = DIR / 'database'
DB_DIR_NAME.mkdir(parents=True, exist_ok=True)

DB_FILE_NAME = DB_DIR_NAME / 'games.sqlite'

BACKUP_DIR_LIST = [
    DIR / 'backup'
]
if additional_backup_dir := os.getenv('ADDITIONAL_BACKUP_DIR'):
    BACKUP_DIR_LIST.append(Path(additional_backup_dir))

PORT_WEB = 5500
PORT_GET_GAME_GENRES = 5501
