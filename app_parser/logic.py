#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import time

from common import (
    FINISHED_GAME,
    FINISHED_WATCHED,
    WebUserAlertException,
    log_common,
    log_append_game,
)
from db import ResultEnum, Game, Platform

from app_parser import models
from app_parser.utils import get_price as get_price_game, smart_comparing_names


def get_game_info(game: int | Game) -> models.GameInfo:
    if isinstance(game, int):
        game = Game.get_by_id(game)

    return models.GameInfo(
        id=game.id,
        name=game.name,
        kind=game.kind,
        platform=game.platform.name,
        price=game.price,
        append_date=game.append_date.strftime("%d/%m/%Y %H:%M:%S"),
        append_date_timestamp=int(game.append_date.timestamp()),
        genres=[genre.name for genre in game.get_genres()],
    )


def get_games_info(games: list[int | Game]) -> list[models.GameInfo]:
    return [get_game_info(game) for game in games]


def get_games() -> list[models.GameInfo]:
    """
    Функция возвращает список игр

    """

    query = (
        Game
        .select()
        .where(Game.kind.in_([FINISHED_GAME, FINISHED_WATCHED]))
        .order_by(Game.append_date.desc())
    )
    return [get_game_info(game) for game in query]


def search(text: str) -> list[models.GameInfo]:
    """
    Функция возвращает список игр

    """

    return [game for game in get_games() if smart_comparing_names(game.name, text)]


def get_price(game_name: str) -> int | None:
    """
    Функция возвращает цену игры.
    Если такой игры нет, вернется None.

    """

    game = Game.select(Game.price).where(Game.name == game_name).first()
    if game:
        return game.price


def has_game(game_name: str) -> bool:
    return Game.select(Game.id).where(Game.name == game_name).exists()


def set_price_game(game_name: str, price: int | None) -> list[int]:
    """
    Функция найдет игры с указанным названием и изменит их цену в базе.
    Возвращает список id игр с измененной ценой.

    """

    game_name = game_name.strip()

    if isinstance(price, str):
        price = price.strip()

    if not game_name or price == "" or price is None:
        error_text = f"Не указано game ( = {game_name!r}) или price ( = {price!r})"
        log_common.error(error_text)
        raise WebUserAlertException(error_text)

    if price is not None and not isinstance(price, int):
        price = int(price)

    ids = []
    for game in Game.select().where(Game.name == game_name):
        game.set_price(price)
        ids.append(game.id)

    return ids


def set_genres(game_name: str, genres: list[str]) -> list[int]:
    """
    Функция найдет игры с указанным названием и установит им жанры.
    Возвращает список id игр с измененными жанрами.

    """

    game_name = game_name.strip()

    if not game_name:
        error_text = f"Не указано название игры ( = {game_name!r})"
        log_common.error(error_text)
        raise WebUserAlertException(error_text)

    ids = []
    for game in Game.select().where(Game.name == game_name):
        result = game.set_genres(genres)

        # Если были какие-то изменения списка жанров у игры и
        # в статистике по добавленным или удаленным не нули
        if result[ResultEnum.ADDED] or result[ResultEnum.DELETED]:
            ids.append(game.id)

    return ids


def rename_game(old_name: str, new_name: str) -> models.RenameGameResult:
    """
    Функция меняет название указанной игры и возвращает словарь с результатом работы.

    """

    old_name = old_name.strip()
    new_name = new_name.strip()

    if not old_name or not new_name:
        error_text = (
            f"Не указано old_name ( = {old_name!r}) или new_name ( = {new_name!r})"
        )
        log_common.error(error_text)
        raise WebUserAlertException(error_text)

    if not has_game(old_name):
        error_text = f"Игры с названием {old_name!r} не существует"
        log_common.error(error_text)
        raise WebUserAlertException(error_text)

    if has_game(new_name):
        error_text = (
            f"Нельзя переименовать {old_name!r}, т.к. имя {new_name!r} уже занято"
        )
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
        result = check_and_fill_price_of_game(new_name)
        id_games_with_changed_price, price = result.game_ids, result.price
    else:
        id_games_with_changed_price, price = None, None

    return models.RenameGameResult(
        game_ids_with_changed_name=id_games_with_changed_name,
        game_ids_with_changed_price=id_games_with_changed_price,
        new_name=new_name,
        price=price,
    )


def delete_game(game: Game):
    """
    Функция удаляет указанную игру.
    Возможна отправка исключения <WebUserAlertException> при ошибке.

    """

    try:
        game.delete_instance()

    except Exception as e:
        error_text = f"При удалении игры {game.name!r} ({game.platform!r}, {game.kind!r}) произошла ошибка: {e}"
        log_common.error(error_text)
        raise WebUserAlertException(error_text)


def set_checked_price_of_game(game_name: str, check=True):
    game_name = game_name.strip()

    for game in Game.select().where(Game.name == game_name):
        game.has_checked_price = check
        game.save()


def check_price_all_non_price_games() -> list[models.PriceUpdateResult]:
    """
    Принудительная проверка цены у игр без цены. То, что цены игр уже проверялись для этой функции
    значение не имеет.

    """

    # Список игр с измененной ценой
    games_with_changed_price = []

    query = Game.select().where(Game.price.is_null())
    games = list(query)
    log_common.debug(f"Игр без цены: {len(games)}")

    for game in games:
        result = check_and_fill_price_of_game(game.name)
        if result.price is not None:
            games_with_changed_price.append(result)

        time.sleep(3)

    return games_with_changed_price


def append_games_to_database(
    finished_game_list: list[models.Game],
    finished_watched_game_list: list[models.Game],
) -> tuple[list[int], list[int]]:
    """
    Функция для добавления игр в таблицу базы. Если игра уже есть в базе, то запрос игнорируется.

    """

    def insert_game(game: models.Game) -> int | None:
        name = game.name

        platform = Platform.add(game.platform)

        # Для отсеивания дубликатов
        has = (
            Game.select(Game.id)
            .where(
                Game.name == name,
                Game.platform == platform,
                Game.kind == game.kind,
            )
            .exists()
        )
        if has:
            return

        log_common.info(f"Добавляю новую игру {name!r} ({game.platform}, {game.kind})")
        log_append_game.info(
            f"Добавляю новую игру {name!r} ({game.platform}, {game.kind})"
        )

        return Game.add(name, platform, game.kind).id

    # Добавление в базу пройденных игр
    added_finished_game_ids: list[int] = []
    for game in finished_game_list:
        if game_id := insert_game(game):
            added_finished_game_ids.append(game_id)

    # Добавление в базу просмотренных игр
    added_watched_game_ids: list[int] = []
    for game in finished_watched_game_list:
        if game_id := insert_game(game):
            added_watched_game_ids.append(game_id)

    return added_finished_game_ids, added_watched_game_ids


def get_game_list_with_price(game_name: str) -> list[Game]:
    """
    Функция по названию игры вернет список игр

    """

    query = Game.select().where(Game.name == game_name, Game.price.is_null(False))
    return list(query)


def check_and_fill_price_of_game(
    game_name: str,
    cache: bool = True,
) -> models.PriceUpdateResult:
    """
    Функция ищет цену игры и при нахождении ее ставит ей цену в базе.
    Возвращает кортеж из списка id игр с измененной ценой и саму цену.

    """

    other_price = None

    game_name = game_name.strip()
    if not game_name:
        log_common.warn(f"Не указано game ( = {game_name!r})")
        return models.PriceUpdateResult(
            game_ids=[],
            game_name=game_name,
            price=other_price,
        )

    # Попробуем найти цену игры в базе -- возможно игра уже есть, но в другой категории
    if cache:
        game_list = get_game_list_with_price(game_name)
        if game_list:
            log_common.debug(
                f"get_game_list_with_price(game={game_name!r}): {game_list}"
            )

            # Вытащим id, kind и price найденной игры
            game = game_list[0]
            other_id, other_kind, other_price = game.id, game.kind, game.price

            log_common.info(
                f"Для игры {game_name!r} удалось найти цену {other_price!r} "
                f"из базы, взяв ее из аналога c id={other_id} в категории {other_kind!r}"
            )

            # Отметим что игра искалась в стиме (чтобы она не искалась в нем, если будет вызвана проверка)
            set_checked_price_of_game(game_name)

            log_common.info(f"Нашли игру: {game_name!r} -> {other_price}")
            log_append_game.info(f"Нашли игру: {game_name!r} -> {other_price}")

            return models.PriceUpdateResult(
                game_ids=set_price_game(game_name, other_price),
                game_name=game_name,
                price=other_price,
            )

    # Поищем игру и ее цену в стиме/gog
    other_price = get_price_game(game_name, log_common, log_append_game)

    # Отметим что игра искалась
    set_checked_price_of_game(game_name)

    if other_price is None:
        log_common.info(
            f"Не получилось найти цену игры {game_name!r}, price is {other_price}"
        )
        return models.PriceUpdateResult(
            game_ids=[],
            game_name=game_name,
            price=other_price,
        )

    return models.PriceUpdateResult(
        game_ids=set_price_game(game_name, other_price),
        game_name=game_name,
        price=other_price,
    )


def fill_price_of_games():
    """
    Функция проходит по играм в базе без указанной цены, пытается найти цены и если удачно, обновляет значение.

    Сайтом для поиска цен является стим.

    """

    # Перебор игр и указание их цены
    # Перед перебором собираем все игры и удаляем дубликаты (игры могут и просмотренными, и пройденными)
    # заодно список кортежей из одного имени делаем просто список имен

    query = (
        Game.select()
        .distinct()
        .where(Game.price.is_null(), Game.has_checked_price == False)
    )
    games_list = list(query)
    if not games_list:
        log_common.info("Искать цены играм не нужно")
        return

    log_common.info(f"Нужно найти цену {len(games_list)} играм")

    platform_pc = Platform.get(Platform.name == "PC")

    for game in games_list:
        # Для PC поиск цены выполняется в стиме/gog, для остальных платформ это не поддержано
        if game.platform == platform_pc:
            check_and_fill_price_of_game(game.name)
            time.sleep(3)
        else:
            # Отмечаем, что игру искать не нужно
            set_checked_price_of_game(game.name)


if __name__ == "__main__":
    from peewee import fn

    # Вывести счетчик игр
    query = (
        Game.select(fn.COUNT("*"), fn.SUM(Game.price))
        .tuples()
        .where(Game.kind == FINISHED_GAME)
    )
    finished_number, finished_sum_price = query.first()

    query = (
        Game.select(fn.COUNT("*"), fn.SUM(Game.price))
        .tuples()
        .where(Game.kind == FINISHED_WATCHED)
    )
    finished_watched_number, finished_watched_sum_price = query.first()

    finished_sum_price = int(finished_sum_price)
    finished_watched_sum_price = int(finished_watched_sum_price)

    total_number = finished_number + finished_watched_number
    total_price = finished_sum_price + finished_watched_sum_price

    print(f"{FINISHED_GAME}: {finished_number}, total price: {finished_sum_price}")
    print(
        f"{FINISHED_WATCHED}: {finished_watched_number}, total price: {finished_watched_sum_price}"
    )
    print(f"Total {total_number}, total price: {total_price}")
    print()

    print(get_price("A Story About My Uncle"))
    print(get_price("A Story About My "))
