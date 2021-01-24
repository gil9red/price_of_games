#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
import time
from typing import List, Tuple, Dict, Any, Optional

from common import (
    FINISHED, FINISHED_WATCHED, WebUserAlertException,
    log_common, log_append_game,
)
from db import Game, fn

from app_parser.utils import steam_search_game_price_list, smart_comparing_names


def get_games_by_kind(kind: str) -> List[Dict[str, Any]]:
    """
    Функция возвращает список игр из словарей с ключами: id, name, price, append_date.

    """

    query = (
        Game.select(
            Game.id, Game.name, Game.price, Game.append_date
        )
        .where(Game.kind == kind)
        .order_by(Game.append_date.desc())
    )
    return [
        {
            'id': game.id,
            'name': game.name,
            'price': float(game.price),  # TODO: цены и так нужно как числа хранить
            'append_date': game.append_date_dt.strftime('%d/%m/%Y %H:%M:%S'),
            'append_date_timestamp': int(game.append_date_dt.timestamp()),
        }
        for game in query
    ]


def get_finished_games() -> List[Dict[str, Any]]:
    """
    Функция возвращает список завершенных игр как кортеж из (id, name, price)

    """

    return get_games_by_kind(FINISHED)


def get_finished_watched_games() -> List[Dict[str, Any]]:
    """
    Функция возвращает список просмотренных игр как кортеж из (id, name, price)

    """

    return get_games_by_kind(FINISHED_WATCHED)


def get_price(game_name: str) -> Optional[str]:
    """
    Функция возвращает цену игры.
    Если такой игры нет, вернется None.

    """

    game = Game.select(Game.price).where(Game.name == game_name).first()
    if game:
        return game.price


def has_game(game_name: str) -> bool:
    return Game.select(Game.id).where(Game.name == game_name).exists()


def set_price_game(game_name: str, price: str) -> List[int]:
    """
    Функция найдет игры с указанным названием и изменит их цену в базе.
    Возвращает список id игр с измененной ценой.

    """

    game_name = game_name.strip()
    price = price.strip()

    if not game_name or not price:
        error_text = f'Не указано game ( = {game_name!r}) или price ( = {price!r})'
        log_common.error(error_text)
        raise WebUserAlertException(error_text)

    ids = []
    for game in Game.select().where(Game.name == game_name):
        game.price = price
        game.modify_price_date = DT.datetime.now()
        game.save()

        ids.append(game.id)

    return ids


def rename_game(old_name: str, new_name: str) -> Dict[str, Any]:
    """
    Функция меняет название указанной игры и возвращает словарь с результатом работы.

    """

    old_name = old_name.strip()
    new_name = new_name.strip()

    if not old_name or not new_name:
        error_text = f'Не указано old_name ( = {old_name!r}) или new_name ( = {new_name!r})'
        log_common.error(error_text)
        raise WebUserAlertException(error_text)

    if not has_game(old_name):
        error_text = f'Игры с названием {old_name!r} не существует'
        log_common.error(error_text)
        raise WebUserAlertException(error_text)

    if has_game(new_name):
        error_text = f'Нельзя переименовать {old_name!r}, т.к. имя {new_name!r} уже занято'
        log_common.error(error_text)
        raise WebUserAlertException(error_text)

    id_games_with_changed_name = []
    for game in Game.select().where(Game.name == old_name):
        game.name = new_name
        game.save()

        id_games_with_changed_name.append(game.id)

    # Если у игры нет цены, попытаемся ее найти, т.к. после переименования и выполнения
    # check_and_fill_price_of_game что-то могло поменяться
    has = Game.select().where(Game.name == new_name, Game.price.is_null()).exists()
    if has:
        id_games_with_changed_price, price = check_and_fill_price_of_game(new_name)
    else:
        id_games_with_changed_price, price = None, None

    return {
        'id_games_with_changed_name': id_games_with_changed_name,
        'id_games_with_changed_price': id_games_with_changed_price,
        'new_name': new_name,
        'price': price,
    }


def delete_game(game_name: str, kind: str) -> int:
    """
    Функция удаляет указанную игру и возвращает ее id.
    Возможна отправка исключения <WebUserAlertException> при ошибке.

    """

    if not game_name or not kind or (kind != FINISHED and kind != FINISHED_WATCHED):
        error_text = (
            f'Не указано name ( = {game_name!r}) или kind ( = {kind!r}), '
            f'или kind неправильный (может быть {FINISHED!r} или {FINISHED_WATCHED!r}).'
        )
        log_common.error(error_text)
        raise WebUserAlertException(error_text)

    try:
        game = Game.get_or_none(Game.name == game_name, Game.kind == kind)
        if not game:
            error_text = f'Не получилось найти игру с name={game_name!r}) и kind={kind!r}'
            log_common.error(error_text)
            raise WebUserAlertException(error_text)

        id_game = game.id
        game.delete_instance()

        return id_game

    except WebUserAlertException as e:
        raise e

    except Exception as e:
        error_text = f'При удалении игры {game_name!r} ({kind!r}) произошла ошибка: {e}'
        raise WebUserAlertException(error_text)


def set_check_game_by_steam(game_name: str, check=True):
    game_name = game_name.strip()

    for game in Game.select().where(Game.name == game_name):
        game.check_steam = check
        game.save()


def check_price_all_non_price_games() -> List[Tuple[List[int], str, str]]:
    """
    Принудительная проверка цены у игр без цены. То, что цены игр уже проверялись для этой функции
    значение не имеет.

    """

    # Список игр с измененной ценой
    games_with_changed_price = []

    query = Game.select().where(Game.price.is_null())
    games = list(query)
    log_common.debug(f'Игр без цены: {len(games)}')

    for game in games:
        id_games, price = check_and_fill_price_of_game(game.name)
        if price:
            games_with_changed_price.append((id_games, game.name, price))

        time.sleep(3)

    return games_with_changed_price


def append_games_to_database(finished_game_list: List[str], finished_watched_game_list: List[str]) -> Tuple[int, int]:
    """
    Функция для добавление игр в таблицу базы. Если игра уже есть в базе, то запрос игнорируется.

    """

    def insert_game(name: str, kind: str) -> bool:
        # Для отсеивания дубликатов
        has = Game.select(Game.id).where(Game.name == name, Game.kind == kind).exists()
        if has:
            return False

        log_common.info(f'Добавляю новую игру {name!r} ({kind})')
        log_append_game.info(f'Добавляю новую игру {name!r} ({kind})')

        Game.create(name=name, kind=kind)
        return True

    # Добавление в базу пройденных игр
    added_finished_games = 0
    for name in finished_game_list:
        added_finished_games += insert_game(name, FINISHED)

    # Добавление в базу просмотренных игр
    added_watched_games = 0
    for name in finished_watched_game_list:
        added_watched_games += insert_game(name, FINISHED_WATCHED)

    return added_finished_games, added_watched_games


def get_game_list_with_price(game_name: str) -> List[Tuple[int, str, str]]:
    """
    Функция по названию игры вернет список игр с их id, kind и price

    """

    query = Game.select().where(Game.name == game_name, Game.price.is_null(False))
    return [(game.id, game.kind, game.price) for game in query]


def check_and_fill_price_of_game(game_name: str, cache=True) -> Tuple[List[int], Optional[str]]:
    """
    Функция ищет цену игры и при нахождении ее ставит ей цену в базе.
    Возвращает кортеж из списка id игр с измененной ценой и саму цену.

    """

    game_name = game_name.strip()
    if not game_name:
        log_common.warn(f'Не указано game ( = {game_name!r})')
        return [], None

    other_price = None

    # Попробуем найти цену игры в базе -- возможно игра уже есть, но в другой категории
    if cache:
        game_list = get_game_list_with_price(game_name)
        if game_list:
            log_common.debug(f'get_game_list_with_price(game={game_name!r}): {game_list}')

            # Вытащим id, kind и price найденной игры
            other_id, other_kind, other_price = game_list[0]

            log_common.info(
                f'Для игры {game_name!r} удалось найти цену {other_price!r} '
                f'из базы, взяв ее из аналога c id={other_id} в категории {other_kind!r}'
            )

            # Отметим что игра искалась в стиме (чтобы она не искалась в нем, если будет вызвана проверка)
            set_check_game_by_steam(game_name)

            log_common.info(f'Нашли игру: {game_name!r} -> {other_price}')
            log_append_game.info(f'Нашли игру: {game_name!r} -> {other_price}')

            return set_price_game(game_name, other_price), other_price

    # Поищем игру и ее цену в стиме
    game_price_list = steam_search_game_price_list(game_name)

    # Отметим что игра искалась в стиме
    set_check_game_by_steam(game_name)

    # Сначала пытаемся найти игру по полному совпадению
    for name, price in game_price_list:
        if game_name == name:
            other_price = price
            break

    # Если по полному совпадению на нашли, пытаемся найти предварительно очищая названия игр
    # от лишних символов
    if other_price is None:
        for name, price in game_price_list:
            # Если нашли игру, запоминаем цену и прерываем сравнение с другими найденными играми
            if smart_comparing_names(game_name, name):
                other_price = price
                break

    if other_price == 0 or other_price is None:
        log_common.info(f'Не получилось найти цену игры {game_name!r}, price is {other_price}')
        return [], None

    log_common.info(f'Нашли игру: {game_name!r} ({name}) -> {other_price}')
    log_append_game.info(f'Нашли игру: {game_name!r} ({name}) -> {other_price}')

    return set_price_game(game_name, other_price), other_price


def fill_price_of_games():
    """
    Функция проходит по играм в базе без указанной цены, пытается найти цены и если удачно, обновляет значение.

    Сайтом для поиска цен является стим.

    """

    # Перебор игр и указание их цены
    # Перед перебором собираем все игры и удаляем дубликаты (игры могут и просмотренными, и пройденными)
    # заодно список кортежей из одного имени делаем просто списом имен

    query = Game.select().distinct().where(
        Game.price.is_null(),
        Game.check_steam == False
    )
    games_list = list(query)
    if not games_list:
        log_common.info("У всех игр установлены цены")
        return

    log_common.info(f"Нужно найти цену {len(games_list)} играм")

    for game in games_list:
        check_and_fill_price_of_game(game.name)
        time.sleep(3)


if __name__ == '__main__':
    # Вывести счетчик игр
    query = Game.select(fn.COUNT('*'), fn.SUM(Game.price)).tuples().where(
        Game.kind == FINISHED
    )
    finished_number, finished_sum_price = query.first()

    query = Game.select(fn.COUNT('*'), fn.SUM(Game.price)).tuples().where(
        Game.kind == FINISHED_WATCHED
    )
    finished_watched_number, finished_watched_sum_price = query.first()

    total_number = finished_number + finished_watched_number
    total_price = finished_sum_price + finished_watched_sum_price

    print(f'{FINISHED}: {finished_number}, total price: {finished_sum_price}')
    print(f'{FINISHED_WATCHED}: {finished_watched_number}, total price: {finished_watched_sum_price}')
    print(f'Total {total_number}, total price: {total_price}')
    print()

    print(get_price('A Story About My Uncle'))
    print(get_price('A Story About My '))
