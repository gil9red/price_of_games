#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from flask import Blueprint, render_template, send_from_directory

from app_web.auth import auth
from db import Game, Platform
from third_party.mini_played_games_parser import FINISHED_GAME, FINISHED_WATCHED


DIR: Path = Path(__file__).resolve().parent


def get_year_by_number() -> list[tuple[int, int]]:
    items: list[tuple[int, int]] = list(
        Counter(
            [g.append_date.year for g in Game.select(Game.append_date)]
        ).most_common()
    )
    items.sort(key=lambda obj: obj[0], reverse=True)

    return items


def get_games() -> list[Game]:
    return list(Game.select().order_by(Game.append_date.desc()))


def get_games_by_year(year: int) -> list[Game]:
    return [game for game in get_games() if game.append_date.year == year]


def get_day_by_games(year: int) -> dict[str, list[Game]]:
    day_by_games = defaultdict(list)

    for game in get_games_by_year(year):
        day = game.append_date.strftime("%d/%m/%Y")
        day_by_games[day].append(game)

    return day_by_games


def get_platforms() -> list[str]:
    return list(
        platform.name for platform in Platform.select().order_by(Platform.name.asc())
    )


bp: Blueprint = Blueprint(
    name="lenta",
    import_name=__name__,
    template_folder="templates",
    static_folder="static",
)


@bp.route("/")
@auth.login_required
def index():
    year_by_number: list[tuple[int, int]] = get_year_by_number()
    last_year: int = year_by_number[0][0] if year_by_number else date.today().year

    games: list[Game] = get_games()
    total_finished_game: int = len(
        [game for game in games if game.kind == FINISHED_GAME]
    )
    total_finished_watched: int = len(
        [game for game in games if game.kind == FINISHED_WATCHED]
    )

    return render_template(
        "lenta/index.html",
        title="Лента игр",
        year_by_number=year_by_number,
        day_by_games=get_day_by_games(last_year),
        finished_game=FINISHED_GAME,
        finished_watched=FINISHED_WATCHED,
        finished_game_title="🎮 Пройденные",
        finished_watched_title="📺 Просмотренные",
        total_finished_game=total_finished_game,
        total_finished_watched=total_finished_watched,
        all_platforms=get_platforms(),
    )


@bp.route("/year/<int:year>")
def year(year: int):
    return render_template(
        "lenta/year_by_game.html",
        day_by_games=get_day_by_games(year),
    )


@bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        directory=Path(bp.root_path) / "static/images",
        path="favicon.png",
    )
