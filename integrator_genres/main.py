#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from pathlib import Path
from urllib.parse import quote

from config import PORT_GET_GAME_GENRES
from common import get_logger
from db import Game, Genre, ResultEnum

import requests


log = get_logger(Path(__file__).resolve().parent.name)


URL_BASE = f"http://127.0.0.1:{PORT_GET_GAME_GENRES}"
URL_GAME = f"{URL_BASE}/api/game"
URL_GENRES = f"{URL_BASE}/api/genres"
URL_BASE: str = f"http://127.0.0.1:{PORT_GET_GAME_GENRES}"
URL_GAME: str = f"{URL_BASE}/api/game"
URL_GENRES: str = f"{URL_BASE}/api/genres"


def get_empty_result_by_number() -> dict[ResultEnum, int]:
    return {result: 0 for result in sorted(ResultEnum, key=lambda x: x.name)}


def get_result_as_text(result_by_number: dict[ResultEnum, int]) -> str:
    total = sum(result_by_number.values())
    if not total:
        return "изменений нет"

    return ", ".join(
        f"{result.name}: {number}" for result, number in result_by_number.items()
    )


def process_genre(name: str, description: str, aliases: str = "") -> ResultEnum:
    result, _ = Genre.add_or_update(
        name=name,
        description=description,
        aliases=aliases,
    )
    match result:
        case ResultEnum.ADDED:
            log.info(f"Добавлен жанр {name!r}")
        case ResultEnum.UPDATED:
            log.info(f"Обновлен жанр {name!r}")

    return result


def process_game(game: Game, genres: list[str]) -> list[ResultEnum]:
    results = []

    for genre in genres:
        result, _ = game.add_genre(genre)
        if result == ResultEnum.ADDED:
            log.info(f"В игру {game.name!r} добавлен жанр {genre!r}")

        results.append(result)

    return results


def fill_genres():
    log.info("Запуск заполнения жанров")

    result_by_number: dict[ResultEnum, int] = get_empty_result_by_number()

    rs = requests.get(URL_GENRES)
    for item in rs.json():
        result = process_genre(**item)
        result_by_number[result] += 1

    text = get_result_as_text(result_by_number)
    log.info(f"Результат: {text}")

    log.info("Завершено.\n")


def fill_from_current_games() -> list[int]:
    log.info("Запуск заполнения жанров у игр")

    result_by_number: dict[ResultEnum, int] = get_empty_result_by_number()
    ids: list[int] = []

    for game in Game.get_games_without_genres():
        url = f"{URL_GAME}/{quote(game.name)}"

        rs = requests.get(url)
        rs.raise_for_status()

        item = rs.json()
        if not item:
            continue

        results = process_game(game, genres=item["genres"])
        for result in results:
            result_by_number[result] += 1

        # Если хотя бы один жанр был добавлен
        if ResultEnum.ADDED in results:
            ids.append(game.id)

    text = get_result_as_text(result_by_number)
    log.info(f"Результат: {text}")

    log.info("Завершено.\n")

    return ids


def run():
    fill_genres()
    fill_from_current_games()


if __name__ == "__main__":
    run()
