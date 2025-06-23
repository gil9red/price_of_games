#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from flask import session, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

import config


auth = HTTPBasicAuth()


USERS: dict[str, str] = {
    login: generate_password_hash(password)
    for login, password in config.USERS.items()
}


@auth.verify_password
def verify_password(username: str, password: str) -> str | bool | None:
    # Не проверять для 127.0.0.1
    if request.remote_addr == "127.0.0.1":
        return True

    # Запрос без авторизации, попробуем проверить куки
    if not username or not password:
        username = session.get("x-auth-username")
        password = session.get("x-auth-password")

    # Если проверка успешна, то сохраним логин/пароль, чтобы можно было авторизоваться из куков
    # Сессии зашифрованы секретным ключом, поэтому можно хранить как есть
    if username in USERS and check_password_hash(USERS.get(username), password):
        session["x-auth-username"] = username
        session["x-auth-password"] = password
        session.permanent = True

        return username
