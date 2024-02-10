#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import DIR_LOGS
from third_party import mini_played_games_parser


class WebUserAlertException(Exception):
    """
    Исключение, которое будет показано пользователю на странице.
    """


FINISHED_GAME = mini_played_games_parser.FINISHED_GAME
FINISHED_WATCHED = mini_played_games_parser.FINISHED_WATCHED


def get_logger(
    logger_name: str,
    dir_name: Path = DIR_LOGS,
    log_stdout: bool = True,
    log_file: bool = True,
) -> logging.Logger:
    log = logging.getLogger(logger_name)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] %(filename)s[LINE:%(lineno)d] %(levelname)-8s %(message)s"
    )

    if log_file:
        dir_name.mkdir(parents=True, exist_ok=True)
        file_name = dir_name / f"{logger_name}.log"

        fh = RotatingFileHandler(
            file_name, maxBytes=10_000_000, backupCount=5, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        log.addHandler(fh)

    if log_stdout:
        ch = logging.StreamHandler(stream=sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        log.addHandler(ch)

    return log


log_common = get_logger("common")
log_append_game = get_logger("append_game", log_stdout=False)
