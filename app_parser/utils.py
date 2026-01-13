#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import time
import re
import unicodedata

from logging import Logger
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin
from typing import Callable

from bs4 import BeautifulSoup
import requests

from app_parser.models import Game
from config import BACKUP_DIR_LIST
from common import log_common
from third_party.add_notify_telegram import add_notify
from third_party.mini_played_games_parser import parse_played_games
from third_party.get_price_game.from_gog_v2 import get_games as get_games_from_gog


@dataclass
class SearchResult:
    name: str
    price: int | None


session = requests.Session()
session.headers[
    "User-Agent"
] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"

# Думаю, это станет дополнительной гарантией получения русскоязычной версии сайта
session.headers["Accept-Language"] = "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3"


def get_games() -> list[Game]:
    rs = session.get("https://gist.github.com/gil9red/2f80a34fb601cd685353")

    root = BeautifulSoup(rs.content, "html.parser")
    href = root.select_one(".file-actions > a")["href"]
    raw_url = urljoin(rs.url, href)

    rs = session.get(raw_url)
    content_gist = rs.text

    # Скрипт может сохранять скачанные гисты
    for path in BACKUP_DIR_LIST:
        path.mkdir(parents=True, exist_ok=True)

        # Сохранение файла гиста в папку бекапа
        try:
            file_name = str(datetime.today().date()) + ".txt"
            file_name = path / file_name

            file_name.write_text(content_gist, "utf-8")

        except Exception:
            log_common.exception("Error:")

    errors: list[str] = []
    platforms = parse_played_games(content_gist, errors=errors)
    for error_text in errors:
        log_common.info(f"Отправка уведомления: {error_text!r}")
        add_notify(name="Цены игр", message=error_text)

    items: list[Game] = []
    for platform, categories in platforms.items():
        for category, games in categories.items():
            for name in games:
                game = Game(name=name, platform=platform, kind=category)
                items.append(game)

    return items


def get_prepared_price(price: str) -> int:
    # "799,99" -> "799.99"
    price = price.replace(",", ".")

    price = re.sub(r"[^\d.]", "", price)
    price = int(float(price))  # Всегда храним как целые числа

    return price


def steam_search_game_price_list(
    name: str,
    log_common: Logger | None = None,
) -> list[SearchResult]:
    """
    Функция принимает название игры, после ищет его в стиме и возвращает результат как список
    кортежей из (название игры, цена).

    """

    log_common and log_common.debug(f'Поиск в стиме "{name}"')

    # Дополнения с категорией Game не ищутся, например: "Pillars of Eternity: The White March Part I", поэтому url
    # был упрощен для поиска всего
    url = "https://store.steampowered.com/search/"

    # Из цикла не выйти, пока не получится скачать и распарсить страницу
    while True:
        try:
            rs = session.get(url, params=dict(term=name, ndl=1))
            root = BeautifulSoup(rs.content, "html.parser")
            break

        except Exception:
            log_common and log_common.exception(
                "При поиске в стиме что-то пошло не так:"
            )

            # Если произошла какая-то ошибка попытаемся через 5 минут попробовать снова
            time.sleep(5 * 60)

    game_price_list = []

    for div in root.select(".search_result_row"):
        game: str = div.select_one(".title").text.strip()

        # Ищем тег скидки, чтобы вытащить оригинальную цену, а не ту, что получилась со скидкой
        price_el = div.select_one(".discount_original_price") or div.select_one(
            ".discount_final_price"
        )

        # Если цены нет (например, игра еще не продается)
        if not price_el:
            price = None
        else:
            price = price_el.get_text(strip=True)

            # Если в цене нет цифры считаем, что это "Free To Play" или что-то подобное
            m = re.search(r"\d", price)
            if not m:
                price = 0
            else:
                price = get_prepared_price(price)

        game_price_list.append(
            SearchResult(
                name=game,
                price=price,
            )
        )

    log_common and log_common.debug(
        f"game_price_list ({len(game_price_list)}): {game_price_list}"
    )

    time.sleep(0.5)

    return game_price_list


def gog_search_game_price_list(
    name: str,
    log_common: Logger | None = None,
) -> list[SearchResult]:
    """
    Функция принимает название игры, после ищет его в gog и возвращает результат как список
    кортежей из (название игры, цена).

    """

    log_common and log_common.debug(f'Поиск в gog "{name}"')

    game_price_list = []

    for game, price in get_games_from_gog(name):
        game_price_list.append(
            SearchResult(
                name=game,
                price=get_prepared_price(price),
            )
        )

    log_common and log_common.debug(
        f"game_price_list ({len(game_price_list)}): {game_price_list}"
    )

    time.sleep(0.5)

    return game_price_list


def smart_comparing_names(name_1: str, name_2: str) -> bool:
    """
    Функция для сравнивания двух названий игр.
    Возвращает True, если совпадают, иначе - False.

    """

    # SOURCE: https://stackoverflow.com/a/518232/5909792
    def strip_accents(s: str) -> str:
        return "".join(
            c
            for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )

    def to_roman(n: int) -> str:
        # Диапазон чисел от 1..4999
        if not (0 < n < 5000):
            return str(n)  # NOTE: Не валидная ситуация, но для текущего сценария это нормально

        result: str = ""
        for numeral, integer in (
            ("M", 1000),
            ("CM", 900),
            ("D", 500),
            ("CD", 400),
            ("C", 100),
            ("XC", 90),
            ("L", 50),
            ("XL", 40),
            ("X", 10),
            ("IX", 9),
            ("V", 5),
            ("IV", 4),
            ("I", 1),
        ):
            while n >= integer:
                result += numeral
                n -= integer
        return result

    def process_name(name: str) -> str:
        # Приведение к одному регистру
        name = name.lower()

        name = re.sub(
            r"(\w+('\w+)?)\s+(Edition|Издание)",
            "",
            name,
            flags=re.IGNORECASE,
        )

        # Удаление символов кроме буквенных, цифр и _:
        # "the witcher®3:___ вася! wild hunt" -> "thewitcher3___васяwildhunt"
        name = re.sub(r"\W", "", name)

        # Удаление постфиксов
        for postfix in ("dlc", "expansion"):
            name = name.removesuffix(postfix)

        # Удаление версии
        name = re.sub(r"v\d+", "", name)

        # Замена арабских цифр на римские для более точного сравнения
        name = re.sub(r"\d+", lambda m: to_roman(int(m.group())), name)

        name = strip_accents(name)

        return name.lower()

    if "/" in name_1 or "/" in name_2:
        def _get_names(name: str) -> list[str]:
            return name.strip("/").split("/")

        for part_name_1 in _get_names(name_1):
            for part_name_2 in _get_names(name_2):
                if process_name(part_name_1) == process_name(part_name_2):
                    return True

    return process_name(name_1) == process_name(name_2)


def _search_price_from_game_price_list(
    game_name: str,
    game_price_list: list[SearchResult],
    _log_on_found_price: Callable[[str, SearchResult], None],
) -> int | None:
    # Сначала пытаемся найти игру по полному совпадению
    for result in game_price_list:
        if game_name == result.name:
            _log_on_found_price(game_name, result)
            return result.price

    # Если по полному совпадению не нашли, пытаемся найти предварительно очищая названия игр от лишних символов
    for result in game_price_list:
        # Если нашли игру, запоминаем цену и прерываем сравнение с другими найденными играми
        if smart_comparing_names(game_name, result.name):
            _log_on_found_price(game_name, result)
            return result.price


def get_price(
    game_name: str,
    log_common: Logger | None = None,
    log_append_game: Logger | None = None,
) -> int | None:
    def _log_on_found_price(
        game_name: str,
        result: SearchResult,
    ):
        log_common and log_common.info(
            f"Нашли игру: {game_name!r} ({result.name}) -> {result.price}"
        )
        log_append_game and log_append_game.info(
            f"Нашли игру: {game_name!r} ({result.name}) -> {result.price}"
        )

    # Префикс может мешать в поиске, т.к. в названиях магазинов его не включают
    game_name = game_name.replace(" (DLC)", "")

    # Поищем игру и ее цену в стиме
    game_price_list = steam_search_game_price_list(game_name, log_common)
    price = _search_price_from_game_price_list(
        game_name,
        game_price_list,
        _log_on_found_price,
    )
    if price is not None:
        return price

    log_common and log_common.info("Не удалось найти в стиме, поиск в GOG")

    # Поищем игру и ее цену в gog
    game_price_list = gog_search_game_price_list(game_name, log_common)
    return _search_price_from_game_price_list(
        game_name,
        game_price_list,
        _log_on_found_price,
    )


if __name__ == "__main__":
    pass

    # game_name = "Prodeus"
    # print("steam:", steam_search_game_price_list(game_name))
    # print("gog:", gog_search_game_price_list(game_name))
    # print(get_price(game_name))
    #
    # print()
    #
    # game_name = "Alone in the Dark: Illumination"
    # print("steam:", steam_search_game_price_list(game_name))
    # print("gog:", gog_search_game_price_list(game_name))
    # print(get_price(game_name))
