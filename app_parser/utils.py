#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
from logging import Logger
import time
import re
from typing import List, Tuple, Union, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests

from config import BACKUP_DIR_LIST
from common import log_common
from third_party.mini_played_games_parser import parse_played_games


session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'

# Думаю, это станет дополнительной гарантией получения русскоязычной версии сайта
session.headers['Accept-Language'] = 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'


def get_games_list() -> Tuple[List[str], List[str]]:
    """
    Функция возвращает кортеж из двух списков: список пройденных игр и список просмотренных игр

    """

    rs = session.get('https://gist.github.com/gil9red/2f80a34fb601cd685353')

    root = BeautifulSoup(rs.content, 'html.parser')
    href = root.select_one('.file-actions > a')['href']
    raw_url = urljoin(rs.url, href)

    rs = session.get(raw_url)
    content_gist = rs.text

    # Скрипт может сохранять скачанные гисты
    for path in BACKUP_DIR_LIST:
        path.mkdir(parents=True, exist_ok=True)

        # Сохранение файла гиста в папку бекапа
        try:
            file_name = str(DT.datetime.today().date()) + '.txt'
            file_name = path / file_name

            file_name.write_text(content_gist, 'utf-8')

        except Exception:
            log_common.exception("Error:")

    platforms = parse_played_games(content_gist)

    # Пройденные игры
    finished_game_list = platforms['PC']['FINISHED_GAME']

    # Просмотренные игры
    finished_watched_game_list = platforms['PC']['FINISHED_WATCHED']

    return finished_game_list, finished_watched_game_list


def steam_search_game_price_list(name: str) -> List[Tuple[str, Union[float, int]]]:
    """
    Функция принимает название игры, после ищет его в стиме и возвращает результат как список
    кортежей из (название игры, цена).

    """

    log_common.debug('Поиск в стиме "%s"', name)

    # Дополнения с категорией Game не ищутся, например: "Pillars of Eternity: The White March Part I", поэтому url
    # был упрощен для поиска всего
    url = 'https://store.steampowered.com/search/?term=' + name

    # Из цикла не выйти, пока не получится скачать и распарсить страницу
    while True:
        try:
            rs = session.get(url)
            root = BeautifulSoup(rs.content, 'html.parser')
            break

        except Exception:
            log_common.exception('При поиске в стиме что-то пошло не так:')

            # Если произошла какая-то ошибка попытаемся через 5 минут попробовать снова
            time.sleep(5 * 60)

    game_price_list = []

    for div in root.select('.search_result_row'):
        name = div.select_one('.title').text.strip()

        # Ищем тег скидки, чтобы вытащить оригинальную цену, а не ту, что получилась со скидкой
        price_el = div.select_one('.search_price > span > strike') or div.select_one('.search_price')
        price = price_el.get_text(strip=True)

        # Если цены нет (например, игра еще не продается)
        if not price:
            price = None
        else:
            # Если в цене нет цифры считаем, что это "Free To Play" или что-то подобное
            m = re.search(r'\d', price)
            if not m:
                price = 0
            else:
                # Только значение цены
                if 'pуб' not in price:
                    log_common.warn('АХТУНГ! Неизвестный формат цены: "%s".', price)

                price = price.replace(' pуб.', '').strip()

                # "799,99" -> "799.99"
                price = price.replace(',', '.')

        if isinstance(price, str):
            price = re.sub(r'[^\d.]', '', price)
            price = float(price) if '.' in price else int(price)

        game_price_list.append((name, price))

    log_common.debug('game_price_list (%s): %s', len(game_price_list), game_price_list)

    return game_price_list


def smart_comparing_names(name_1: str, name_2: str) -> bool:
    """
    Функция для сравнивания двух названий игр.
    Возвращает True, если совпадают, иначе -- False.

    """

    # Приведение строк к одному регистру
    name_1 = name_1.lower()
    name_2 = name_2.lower()

    def remove_postfix(text: str) -> str:
        for postfix in ('(dlc)', ' expansion'):
            if text.endswith(postfix):
                return text[:-len(postfix)]
        return text

    # Удаление символов кроме буквенных, цифр и _: "the witcher®3:___ вася! wild hunt" -> "thewitcher3___васяwildhunt"
    def clear_name(name: str) -> str:
        return re.sub(r'\W', '', name)

    name_1 = remove_postfix(name_1)
    name_2 = remove_postfix(name_2)

    return clear_name(name_1) == clear_name(name_2)


def get_price(game_name: str, log_common: Logger = None, log_append_game: Logger = None) -> Optional[Union[int, float]]:
    # Поищем игру и ее цену в стиме
    game_price_list = steam_search_game_price_list(game_name)

    # Сначала пытаемся найти игру по полному совпадению
    for name, price in game_price_list:
        if game_name == name:
            log_common.info(f'Нашли игру: {game_name!r} ({name}) -> {price}')
            log_append_game.info(f'Нашли игру: {game_name!r} ({name}) -> {price}')
            return price

    # Если по полному совпадению на нашли, пытаемся найти предварительно очищая названия игр от лишних символов
    for name, price in game_price_list:
        # Если нашли игру, запоминаем цену и прерываем сравнение с другими найденными играми
        if smart_comparing_names(game_name, name):
            log_common.info(f'Нашли игру: {game_name!r} ({name}) -> {price}')
            log_append_game.info(f'Нашли игру: {game_name!r} ({name}) -> {price}')
            return price

    return


if __name__ == '__main__':
    game_name = 'JUMP FORCE'
    print(steam_search_game_price_list(game_name))
    print(get_price(game_name))

    print()

    game_name = 'Alone in the Dark: Illumination'
    print(steam_search_game_price_list(game_name))
    print(get_price(game_name))
