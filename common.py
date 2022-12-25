#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import logging
import sys
from pathlib import Path

from config import DIR_LOG
from third_party import mini_played_games_parser


class WebUserAlertException(Exception):
    """
    Исключение, которое будет показано пользователю на странице.
    """


FINISHED_GAME = mini_played_games_parser.FINISHED_GAME
FINISHED_WATCHED = mini_played_games_parser.FINISHED_WATCHED


def get_logger(file_name: str, dir_name=DIR_LOG, log_stdout=True, log_file=True):
    dir_name = Path(dir_name).resolve()
    dir_name.mkdir(parents=True, exist_ok=True)

    file_name = str(dir_name / Path(file_name).resolve().name) + '.log'

    log = logging.getLogger(file_name)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] %(filename)s[LINE:%(lineno)d] %(levelname)-8s %(message)s')

    if log_file:
        fh = logging.FileHandler(file_name, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        log.addHandler(fh)

    if log_stdout:
        ch = logging.StreamHandler(stream=sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        log.addHandler(ch)

    return log


log_common = get_logger('common')
log_append_game = get_logger('append_game', log_stdout=False)
