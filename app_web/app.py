#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import logging
import sys

from datetime import timedelta
from logging.handlers import RotatingFileHandler

from flask import Flask

from app_web.lenta import bp as lenta_bp
from config import DIR_LOGS, SECRET_KEY


app = Flask("web__price_of_games")
app.json.sort_keys = False
app.permanent_session_lifetime = timedelta(days=365)
app.secret_key = SECRET_KEY

app.register_blueprint(lenta_bp, url_prefix='/lenta')

log: logging.Logger = app.logger
log.handlers.clear()

formatter = logging.Formatter(
    "[%(asctime)s] %(filename)s:%(lineno)d %(levelname)-8s %(message)s"
)

file_handler = RotatingFileHandler(
    DIR_LOGS / "web.log", maxBytes=10_000_000, backupCount=5, encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)

log.setLevel(logging.DEBUG)
log.addHandler(file_handler)
log.addHandler(stream_handler)

log_werkzeug = logging.getLogger("werkzeug")
log_werkzeug.setLevel(logging.DEBUG)
log_werkzeug.addHandler(file_handler)
log_werkzeug.addHandler(stream_handler)
