#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from datetime import datetime

from price_of_games.common import get_logger
from price_of_games.db import Game


log = get_logger(__name__)


for game in Game.select():
    if not isinstance(game.append_date, datetime):
        append_date = datetime.fromisoformat(game.append_date).replace(tzinfo=None)

        text = (
            f"{game}\n    Update of append_date: {game.append_date} ({type(game.append_date)}) "
            f"-> {append_date} ({type(append_date)})\n"
        )
        log.info(text)

        game.append_date = append_date
        game.save()

    if not isinstance(game.modify_price_date, datetime):
        modify_price_date = datetime.fromisoformat(game.modify_price_date).replace(
            tzinfo=None
        )

        text = (
            f"{game}\n    Update of modify_price_date: {game.modify_price_date} ({type(game.modify_price_date)}) "
            f"-> {modify_price_date} ({type(modify_price_date)})\n"
        )
        log.info(text)

        game.modify_price_date = modify_price_date
        game.save()
