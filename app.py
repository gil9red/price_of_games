#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


LOG_FILENAME = 'log'


from flask import Flask
app = Flask(__name__)
logger = app.logger

import logging
formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(LOG_FILENAME, maxBytes=10000000, backupCount=5, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

import sys
stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

log_werkzeug = logging.getLogger('werkzeug')
log_werkzeug.setLevel(logging.DEBUG)
log_werkzeug.addHandler(file_handler)
log_werkzeug.addHandler(stream_handler)
