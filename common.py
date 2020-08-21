#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


def make_backslashreplace_console():
    # При выводе юникодных символов в консоль винды
    # Возможно, не только для винды, но и для любой платформы стоит использовать
    # эту настройку -- мало какие проблемы могут встретиться
    import sys
    if sys.platform == 'win32':
        import codecs

        try:
            sys.stdout = codecs.getwriter(sys.stdout.encoding)(sys.stdout.detach(), 'backslashreplace')
            sys.stderr = codecs.getwriter(sys.stderr.encoding)(sys.stderr.detach(), 'backslashreplace')

        except AttributeError:
            # ignore "AttributeError: '_io.BufferedWriter' object has no attribute 'encoding'"
            pass


make_backslashreplace_console()


import os
from typing import List, Dict, Any, Union

from config import BACKUP_DIR_LIST, DB_FILE_NAME, BACKUP_GIST, LOG_COMMON, LOG_APPEND_GAME


class WebUserAlertException(Exception):
    """
    Исключение, которое будет показано пользователю на странице.

    Работает только для v2.

    """


FINISHED = 'Finished'
FINISHED_WATCHED = 'Finished watched'


def get_logger(name, file='log.txt', encoding='utf-8', log_stdout=True, log_file=True):
    import logging
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] %(filename)s:%(lineno)d %(levelname)-8s %(message)s')

    if log_file:
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(file, maxBytes=10000000, backupCount=5, encoding=encoding)
        fh.setFormatter(formatter)
        log.addHandler(fh)

    if log_stdout:
        import sys
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(formatter)
        log.addHandler(sh)

    return log


log_common = get_logger('log_common', LOG_COMMON)
log_append_game = get_logger('log_append_game', LOG_APPEND_GAME, log_stdout=False)


def create_connect(fields_as_dict=False):
    import sqlite3
    connect = sqlite3.connect(DB_FILE_NAME)

    if fields_as_dict:
        connect.row_factory = sqlite3.Row

    return connect


def init_db():
    # Создание базы и таблицы
    with create_connect() as connect:
        connect.execute('''
            CREATE TABLE IF NOT EXISTS Game (
                id                INTEGER  PRIMARY KEY,
                name              TEXT     NOT NULL,
                price             TEXT     DEFAULT NULL,
                append_date       DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME')),
                modify_price_date DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME')),
                kind              TEXT     NOT NULL,
                check_steam       BOOLEAN  NOT NULL DEFAULT 0
            );
        ''')

        connect.commit()

        # # NOTE: когда нужно в таблице подправить схему:
        # connect.executescript('''
        #     PRAGMA foreign_keys = 0;
        #
        #     CREATE TABLE temp_table AS SELECT * FROM Game;
        #
        #     DROP TABLE Game;
        #
        #     CREATE TABLE Game (
        #         id                INTEGER  PRIMARY KEY,
        #         name              TEXT     NOT NULL,
        #         price             TEXT     DEFAULT NULL,
        #         append_date       DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME')),
        #         modify_price_date DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME')),
        #         kind              TEXT     NOT NULL,
        #         check_steam       BOOLEAN  NOT NULL DEFAULT 0,
        #
        #         NEW_COLUMN        TEXT     DEFAULT 'FOO'
        #     );
        #
        #     INSERT INTO Game (id, name, price, append_date, modify_price_date, kind, check_steam)
        #                SELECT id, name, price, append_date, modify_price_date, kind, check_steam
        #                FROM temp_table;
        #
        #     DROP TABLE temp_table;
        #
        #     PRAGMA foreign_keys = 1;
        # ''')
        #
        # connect.commit()


def db_create_backup():
    for path in BACKUP_DIR_LIST:
        from datetime import datetime
        file_name = str(datetime.today().date()) + '.sqlite'
        file_name = os.path.join(path, file_name)

        import shutil
        shutil.copy(DB_FILE_NAME, file_name)


def get_games_by_kind(kind: str) -> List[Dict[str, Any]]:
    """
    Функция возвращает список игр как кортеж из (id, name, price)

    """

    with create_connect(fields_as_dict=True) as connect:
        get_game_sql = '''
            SELECT id, name, price, append_date
            FROM game
            WHERE kind = ?
            ORDER BY name
        '''
        return list(map(dict, connect.execute(get_game_sql, (kind,)).fetchall()))


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


def get_id_games_by_name(game_name: str) -> List[int]:
    """
    Функция возвращает список id игр.

    """

    with create_connect() as connect:
        # Получение id игр с указанным названием
        sql = "SELECT id FROM Game WHERE name = ?"
        return [id_ for (id_,) in connect.execute(sql, (game_name,)).fetchall()]


def get_price(game_name: str) -> Union[str, None]:
    """
    Функция возвращает цену игры.
    Если такой игры нет, вернется None.

    """

    with create_connect() as connect:
        sql = "SELECT price FROM Game WHERE name = ?"
        price = connect.execute(sql, (game_name,)).fetchone()
        if price:
            return price[0]

        return price


def has_game(game_name: str) -> bool:
    with create_connect() as connect:
        has = connect.execute("SELECT 1 FROM Game WHERE name = ?", (game_name,)).fetchone()
        return bool(has)


def set_price_game(game: str, price: str) -> List[int]:
    """
    Функция найдет игры с указанным названием и изменит их цену в базе.
    Возвращает список id игр с измененной ценой.

    """

    game = game.strip()
    price = price.strip()

    if not game or not price:
        error_text = f'Не указано game ( = "{game}") или price ( = "{price}")'
        log_common.debug(error_text)
        raise WebUserAlertException(error_text)

    with create_connect() as connect:
        sql = "UPDATE Game SET price = ?, modify_price_date = DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME') WHERE name = ?"
        connect.execute(sql, (price, game))
        connect.commit()

        # Получение id игр с указанным названием
        return get_id_games_by_name(game)


def rename_game(old_name: str, new_name: str) -> dict:
    """
    Функция меняет название указанной игры и возвращает словарь с результатом работы.

    """

    old_name = old_name.strip()
    new_name = new_name.strip()

    if not old_name or not new_name:
        error_text = f'Не указано old_name ( = "{old_name}") или new_name ( = "{new_name}")'
        log_common.debug(error_text)
        raise WebUserAlertException(error_text)

    with create_connect() as connect:
        if not has_game(old_name):
            error_text = f'Игры с названием "{old_name}" не существует'
            log_common.debug(error_text)
            raise WebUserAlertException(error_text)

        if has_game(new_name):
            error_text = f'Нельзя переименовать "{old_name}", т.к. имя "{new_name}" уже занято'
            log_common.debug(error_text)
            raise WebUserAlertException(error_text)

        connect.execute("UPDATE Game SET name = ? WHERE name = ?", (new_name, old_name))
        connect.commit()

        # Получение id игр с указанным названием
        id_games_with_changed_name = get_id_games_by_name(new_name)

        # Если у игры нет цены, попытаемся ее найти, т.к. после переименования что-то
        # могло поменяться
        id_games_with_changed_price = []
        price = None

        has = connect.execute("SELECT 1 FROM Game WHERE name = ? AND price is null", (new_name,)).fetchone()
        if has:
            id_games_with_changed_price, price = check_and_fill_price_of_game(new_name)

        result = {
            'id_games_with_changed_name': id_games_with_changed_name,
            'id_games_with_changed_price': id_games_with_changed_price,
            'new_name': new_name,
            'price': price,
        }
        return result


def delete_game(name: str, kind: str) -> int:
    """
    Функция удаляет указанную игру и возвращает ее id.
    Возможна отправка исключения <WebUserAlertException> при ошибке.

    """

    if not name or not kind or (kind != FINISHED and kind != FINISHED_WATCHED):
        error_text = f'Не указано name ( = "{name}") или kind ( = "{kind}"), ' \
                     f'или kind неправильный (может быть {FINISHED} или {FINISHED_WATCHED}).'
        log_common.debug(error_text)
        raise WebUserAlertException(error_text)

    try:
        with create_connect() as connect:
            id_game = connect.execute("SELECT id FROM Game WHERE kind = ? AND name = ?", (kind, name)).fetchone()
            if not id_game:
                error_text = f'Не получилось найти игру с name ( = "{name}") и kind ( = "{kind}")'
                log_common.debug(error_text)
                raise WebUserAlertException(error_text)

            id_game = id_game[0]

            connect.execute("DELETE FROM Game WHERE id = ?", (id_game,))
            connect.commit()

        return id_game

    except WebUserAlertException as e:
        raise e

    except Exception as e:
        error_text = f'При удалении игры "{name}" ({kind}) произошла ошибка: {e}'
        raise WebUserAlertException(error_text)


def set_check_game_by_steam(game: str, check=1):
    game = game.strip()

    with create_connect() as connect:
        connect.execute("UPDATE Game SET check_steam = ? WHERE name = ?", (check, game))
        connect.commit()


def get_duplicates() -> list:
    from collections import defaultdict
    name_kind_by_id_dict = defaultdict(list)

    with create_connect() as connect:
        for id_, name, kind in connect.execute('SELECT id, name, kind FROM game').fetchall():
            name_kind_by_id_dict[(name, kind)].append(id_)

    return list(filter(lambda item: len(item[1]) > 1, name_kind_by_id_dict.items()))


def check_price_all_non_price_games() -> list:
    """
    Принудительная проверка цены у игр без цены. То, что цены игр уже проверялись для этой функции
    значение не имеет.

    """

    with create_connect() as connect:
        # Список игр с измененной ценой
        games_with_changed_price = []

        games = connect.execute('SELECT name FROM game WHERE price IS NULL').fetchall()

        # Удаление дубликатов (игры могут повторяться для категорий пройденных и просмотренных)
        games = {name for (name,) in games}
        log_common.debug(f'Игр без цены: {len(games)}')

        for name in games:
            id_games, price = check_and_fill_price_of_game(name)
            if price is not None:
                games_with_changed_price.append((id_games, name, price))

            import time
            time.sleep(3)

        return games_with_changed_price


# Parser from https://github.com/gil9red/played_games/blob/f23777a1368f9124450bedac036791068d8ca099/mini_played_games_parser.py#L7
def parse_played_games(text: str, silence: bool=False) -> dict:
    """
    Функция для парсинга списка игр.
    """

    FINISHED_GAME = 'FINISHED_GAME'
    NOT_FINISHED_GAME = 'NOT_FINISHED_GAME'
    FINISHED_WATCHED = 'FINISHED_WATCHED'
    NOT_FINISHED_WATCHED = 'NOT_FINISHED_WATCHED'

    FLAG_BY_CATEGORY = {
        '  ': FINISHED_GAME,
        '- ': NOT_FINISHED_GAME,
        ' -': NOT_FINISHED_GAME,
        ' @': FINISHED_WATCHED,
        '@ ': FINISHED_WATCHED,
        '-@': NOT_FINISHED_WATCHED,
        '@-': NOT_FINISHED_WATCHED,
    }

    # Регулярка вытаскивает выражения вида: 1, 2, 3 или 1-3, или римские цифры: III, IV
    import re
    PARSE_GAME_NAME_PATTERN = re.compile(
        r'(\d+(, *?\d+)+)|(\d+ *?- *?\d+)|([MDCLXVI]+(, ?[MDCLXVI]+)+)',
        flags=re.IGNORECASE
    )

    def parse_game_name(game_name: str) -> list:
        """
        Функция принимает название игры и пытается разобрать его, после возвращает список названий.
        У некоторых игр в названии может указываться ее части или диапазон частей, поэтому для правильного
        составления списка игр такие случаи нужно обрабатывать.
        Пример:
            "Resident Evil 4, 5, 6" -> ["Resident Evil 4", "Resident Evil 5", "Resident Evil 6"]
            "Resident Evil 1-3"     -> ["Resident Evil", "Resident Evil 2", "Resident Evil 3"]
            "Resident Evil 4"       -> ["Resident Evil 4"]
        """

        match = PARSE_GAME_NAME_PATTERN.search(game_name)
        if match is None:
            return [game_name]

        seq_str = match.group(0)

        # "Resident Evil 4, 5, 6" -> "Resident Evil"
        # For not valid "Trollface Quest 1-7-8" -> "Trollface Quest"
        index = game_name.index(seq_str)
        base_name = game_name[:index].strip()

        seq_str = seq_str.replace(' ', '')

        if ',' in seq_str:
            # '1,2,3' -> ['1', '2', '3']
            seq = seq_str.split(',')

        elif '-' in seq_str:
            seq = seq_str.split('-')

            # ['1', '7'] -> [1, 7]
            seq = list(map(int, seq))

            # [1, 7] -> ['1', '2', '3', '4', '5', '6', '7']
            seq = list(map(str, range(seq[0], seq[1] + 1)))

        else:
            return [game_name]

        # Сразу проверяем номер игры в серии и если она первая, то не добавляем в названии ее номер
        return [base_name if num == '1' else base_name + " " + num for num in seq]

    platforms = dict()
    platform = None

    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue

        flag = line[:2]
        if flag not in FLAG_BY_CATEGORY and line.endswith(':'):
            platform_name = line[:-1]

            platform = {
                FINISHED_GAME: [],
                NOT_FINISHED_GAME: [],
                FINISHED_WATCHED: [],
                NOT_FINISHED_WATCHED: [],
            }
            platforms[platform_name] = platform

            continue

        if not platform:
            continue

        category_name = FLAG_BY_CATEGORY.get(flag)
        if not category_name:
            if not silence:
                print(f'Странный формат строки: "{line}"')
            continue

        category = platform[category_name]

        game_name = line[2:]
        for game in parse_game_name(game_name):
            if game in category:
                if not silence:
                    print(f'Предотвращено добавление дубликата игры "{game}"')
                continue

            category.append(game)

    return platforms


def get_games_list() -> (list, list):
    """
    Функция возвращает кортеж из двух списков: список пройденных игр и список просмотренных игр

    """

    import requests
    rs = requests.get('https://gist.github.com/gil9red/2f80a34fb601cd685353')

    from bs4 import BeautifulSoup
    root = BeautifulSoup(rs.content, 'html.parser')
    href = root.select_one('.file-actions > a')['href']

    from urllib.parse import urljoin
    raw_url = urljoin(rs.url, href)

    rs = requests.get(raw_url)
    content_gist = rs.text

    # Скрипт может сохранять скачанные гисты
    if BACKUP_GIST:
        for path in BACKUP_DIR_LIST:
            # Если папка не существует, попытаемся создать
            if not os.path.exists(path):
                try:
                    os.mkdir(path)

                except Exception:
                    log_common.exception("Error:")

                    # Если при создании папки возникла ошибка, пытаться сохранить в нее
                    # файл уже бесполезно
                    continue

            # Сохранение файла гиста в папку бекапа
            try:
                from datetime import datetime
                file_name = str(datetime.today().date()) + '.txt'
                file_name = os.path.join(path, file_name)

                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(content_gist)

            except Exception:
                log_common.exception("Error:")

    platforms = parse_played_games(content_gist)

    # Пройденные игры
    finished_game_list = platforms['PC']['FINISHED_GAME']

    # Просмотренные игры
    finished_watched_game_list = platforms['PC']['FINISHED_WATCHED']

    return finished_game_list, finished_watched_game_list


def append_games_to_database(connect, finished_game_list, finished_watched_game_list) -> (int, int):
    """
    Функция для добавление игр в таблицу базы. Если игра уже есть в базе, то запрос игнорируется.

    """

    cursor = connect.cursor()

    def insert_game(name, kind) -> bool:
        # Для отсеивания дубликатов
        has = cursor.execute("SELECT 1 FROM Game WHERE name = ? and kind = ?", (name, kind)).fetchone()
        if has:
            return False

        log_common.debug(f'Добавляю новую игру "{name}" ({kind})')
        log_append_game.debug(f'Добавляю новую игру "{name}" ({kind})')
        cursor.execute("INSERT INTO Game (name, kind) VALUES (?,?)", (name, kind))

        return True

    # Добавлени в базу пройденных игр
    added_finished_games = 0
    for name in finished_game_list:
        added_finished_games += insert_game(name, FINISHED)

    # Добавлени в базу просмотренных игр
    added_watched_games = 0
    for name in finished_watched_game_list:
        added_watched_games += insert_game(name, FINISHED_WATCHED)

    # Сохранение изменений в базе
    connect.commit()

    # Вряд ли такое произойдет...
    duplicates = get_duplicates()
    if duplicates:
        log_common.debug("АХТУНГ! Найдены дубликаты:")
        for (name, kind), id_list in duplicates:
            log_common.debug(f'    {name} / {kind} c id {id_list}')

    return added_finished_games, added_watched_games


def get_game_list_with_price(game: str) -> [int, str, str]:
    """
    Функция по названию игры вернет список игр с их id, kind и price

    """

    with create_connect() as connect:
        sql = "SELECT id, kind, price from Game WHERE name = ? and price is not null"
        return connect.execute(sql, (game,)).fetchall()


def check_and_fill_price_of_game(game: str, cache=True) -> (list, str):
    """
    Функция ищет цену игры и при нахождении ее ставит ей цену в базе.
    Возвращает кортеж из списка id игр с измененной ценой и саму цену.

    """

    game = game.strip()

    if not game:
        log_common.debug(f'Не указано game ( = "{game}")')
        return [], None

    game_price = None

    # Попробуем найти цену игры в базе -- возможно игра уже есть, но в другой категории
    if cache:
        game_list = get_game_list_with_price(game)
        if game_list:
            log_common.debug('get_game_list_with_price(game="%s"): %s', game, game_list)

            # Вытащим id, kind и price найденной игры
            id_, kind, game_price = game_list[0]

            log_common.debug('Для игры "%s" удалось найти цену "%s" из базы, взяв ее из '
                             'аналога c id=%s в категории "%s"', game, game_price, id_, kind)

            # Отметим что игра искалась в стиме (чтобы она не искалась в нем, если будет вызывана проверка)
            set_check_game_by_steam(game)

            log_common.debug('Нашли игру: %s -> %s', game, game_price)
            log_append_game.debug('Нашли игру: %s -> %s', game, game_price)
            return set_price_game(game, game_price), game_price

    # Поищем игру и ее цену в стиме
    game_price_list = steam_search_game_price_list(game)

    # Отметим что игра искалась в стиме
    set_check_game_by_steam(game)

    # Сначала пытаемся найти игру по полному совпадению
    for name, price in game_price_list:
        if game == name:
            game_price = price
            break

    # Если по полному совпадению на нашли, пытаемся найти предварительно очищая названия игр
    # от лишних символов
    if game_price is None:
        for name, price in game_price_list:
            # Если нашли игру, запоминаем цену и прерываем сравнение с другими найденными играми
            if smart_comparing_names(game, name):
                game_price = price
                break

    if game_price == 0 or game_price is None:
        # TODO: заполнять вручную или искать на других сайтах цену
        log_common.debug(f'Не получилось найти цену игры "{game}", price is {game_price}')
        return [], None

    log_common.debug(f'Нашли игру: "{game}" ({name}) -> {game_price}')
    log_append_game.debug(f'Нашли игру: "{game}" ({name}) -> {game_price}')
    return set_price_game(game, game_price), game_price


def fill_price_of_games(connect):
    """
    Функция проходит по играм в базе без указанной цены, пытается найти цены и если удачно, обновляет значение.

    # TODO: больше сайтов поддержать, т.к. на стиме не все игры можно найти.
    Сайтом для поиска цен является стим.

    """

    # Перебор игр и указание их цены
    # Перед перебором собираем все игры и удаляем дубликаты (игры могут и просмотренными, и пройденными)
    # заодно список кортежей из одного имени делаем просто списом имен

    sql_text = 'SELECT name FROM game where price is null and check_steam = 0'

    cursor = connect.cursor()
    games_list = set(game for (game,) in cursor.execute(sql_text).fetchall())

    if not games_list:
        log_common.debug("Игр без указанных цен нет")
        return

    log_common.debug(f"Нужно найти цену {len(games_list)} играм")

    for game in games_list:
        check_and_fill_price_of_game(game)

        import time
        time.sleep(3)


def steam_search_game_price_list(name):
    """
    Функция принимает название игры, после ищет его в стиме и возвращает результат как список
    кортежей из (название игры, цена).

    """

    log_common.debug('Поиск в стиме "%s"', name)

    # category1 = 998 (Game)
    # url = 'http://store.steampowered.com/search/?category1=998&os=win&supportedlang=english&term=' + name

    # TODO: валюта найденных игр определяется по текущему моему ip, поэтому она правильная -- ru, но из-за этого
    # может быть неправильный подсчет цены при запуске на каком-то хосте
    #
    # Дополнения с категорией Game не ищутся, например: "Pillars of Eternity: The White March Part I", поэтому url
    # был упрощен для поиска всего
    url = 'http://store.steampowered.com/search/?term=' + name

    # TODO: проверить http://store.steampowered.com/search/suggest?term=Dig+or+Die&f=games&cc=RU&l=russian&no_violence=0&no_sex=0&v=2651658
    # По идеи, это вариант запроса рабочий, но нужно потестить на разные ситуации: игры, DLC, как выглядят игры со скидкой и без

    headers = {
        # Думаю, это станет дополнитульной гарантией получения русскоязычной версии сайта
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    }

    import requests
    from bs4 import BeautifulSoup

    # Из цикла не выйти, пока не получится скачать и распарсить страницу
    while True:
        try:
            rs = requests.get(url, headers=headers)
            root = BeautifulSoup(rs.content, 'html.parser')

            break

        except:
            log_common.exception('При поиске в стиме что-то пошло не так:')

            # Если произошла какая-то ошибка попытаемся через 5 минут попробовать снова
            import time
            time.sleep(5 * 60)

    game_price_list = []

    for div in root.select('.search_result_row'):
        name = div.select_one('.title').text.strip()

        # Ищем тег скидки, чтобы вытащить оригинальную цены, а не ту, что получилась со скидкой
        if div.select_one('.search_discount > span'):
            price = div.select_one('.search_price > span > strike').text.strip()
        else:
            price = div.select_one('.search_price').text.strip()

        # Если цены нет (например, игра еще не продается)
        if not price:
            price = None
        else:
            # Если в цене нет цифры считаем что это "Free To Play" или что-то подобное
            import re
            match = re.search('\d', price)
            if not match:
                price = '0'
            else:
                # Только значение цены
                if 'pуб' not in price:
                    log_common.debug('АХТУНГ! Неизвестный формат цены: "%s".', price)

                price = price.replace(' pуб.', '').strip()

                # "799,99" -> "799.99"
                price = price.replace(',', '.')

        game_price_list.append((name, price))

    log_common.debug('game_price_list (%s): %s', len(game_price_list), game_price_list)

    return game_price_list


def smart_comparing_names(name_1, name_2):
    """
    Функция для сравнивания двух названий игр.
    Возвращает True, если совпадают, иначе -- False.

    """

    # Приведение строк к одному регистру
    name_1 = name_1.lower()
    name_2 = name_2.lower()

    def remove_postfix(text):
        for postfix in ('(dlc)', ' expansion'):
            if text.endswith(postfix):
                return text[:-len(postfix)]
        return text

    # Удаление символов кроме буквенных, цифр и _: "the witcher®3:___ вася! wild hunt" -> "thewitcher3___васяwildhunt"
    def clear_name(name):
        import re
        return re.sub(r'\W', '', name)

    name_1 = remove_postfix(name_1)
    name_2 = remove_postfix(name_2)

    return clear_name(name_1) == clear_name(name_2)


class Settings:
    """
    Класс представляет собой таблицу в базе.

    """

    def __init__(self, connect=None):
        if connect is None:
            connect = create_connect()

        # Сохраняем для работы с нашей таблицей в базе
        self._connect = connect
        self._cursor = self._connect.cursor()

        # Создание таблицы для хранения настроек по типу: ключ - значение
        self._cursor.execute('''
        CREATE TABLE IF NOT EXISTS Settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        ''')

        self._connect.commit()

    def __setattr__(self, key, value):
        # Для обработки внутренних полей
        if key.startswith("_"):
            return super().__setattr__(key, value)

        self._cursor.execute('INSERT OR REPLACE INTO Settings VALUES (?, ?);', (key, value))
        self._connect.commit()

    def __getattr__(self, key):
        # Для обработки внутренних полей
        if key.startswith("_"):
            return super().__getattr__(key)

        data = self._cursor.execute('SELECT value FROM Settings WHERE key = ?', (key,)).fetchone()
        if data:
            (value,) = data
            return value

    def keys(self):
        return [key for (key,) in self._cursor.execute('SELECT key FROM Settings').fetchall()]

    def values(self):
        return [value for (value,) in self._cursor.execute('SELECT value FROM Settings').fetchall()]

    def items(self):
        return self._cursor.execute('SELECT key, value FROM Settings').fetchall()


if __name__ == '__main__':
    # print(get_games_list())
    # print()

    # Вывести счетчик игр
    with create_connect() as connect:
        sql_text = 'SELECT count(*), sum(price) FROM Game WHERE kind = ?'

        finished_number, finished_sum_price = connect.execute(sql_text, (FINISHED,)).fetchone()
        finished_watched_number, finished_watched_sum_price = connect.execute(sql_text, (FINISHED_WATCHED,)).fetchone()
        total_number = finished_number + finished_watched_number
        total_price = finished_sum_price + finished_watched_sum_price

        print(f'{FINISHED}: {finished_number}, total price: {finished_sum_price}')
        print(f'{FINISHED_WATCHED}: {finished_watched_number}, total price: {finished_watched_sum_price}')
        print(f'Total {total_number}, total price: {total_price}')
        print()

    print(get_price('A Story About My Uncle'))
    print(get_price('A Story About My '))

    # # Print statistic from backup databases
    # import sqlite3
    #
    # from glob import glob
    # for file_name in glob('backup/*.sqlite'):
    #     print(file_name)
    #
    #     with sqlite3.connect(file_name) as connect:
    #         sql_text = 'SELECT count(*), sum(price) FROM Game WHERE kind = ?'
    #
    #         finished_number, finished_sum_price = connect.execute(sql_text, (FINISHED,)).fetchone()
    #         finished_watched_number, finished_watched_sum_price = connect.execute(sql_text,
    #                                                                               (FINISHED_WATCHED,)).fetchone()
    #         total_number = finished_number + finished_watched_number
    #         total_price = finished_sum_price + finished_watched_sum_price
    #
    #         print('    {}: {}, total price: {}'.format(FINISHED, finished_number, finished_sum_price))
    #         print('    {}: {}, total price: {}'.format(FINISHED_WATCHED, finished_watched_number,
    #                                                    finished_watched_sum_price))
    #         print('    Total {}, total price: {}'.format(total_number, total_price))
    #         print()

    # # Получение списка дат добавления игры и рисование по нему графика
    # append_date_list = connect.execute("SELECT append_date "
    #                                    "FROM Game "
    #                                    "WHERE append_date IS NOT NULL "
    #                                    "ORDER BY append_date").fetchall()
    #
    # from datetime import datetime
    #
    # def to_datetime(date_str: str) -> datetime:
    #     return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    #
    # append_date_month_list = []
    #
    # for (item,) in append_date_list:
    #     date = to_datetime(item)
    #     date = datetime(date.year, date.month, 1)
    #
    #     append_date_month_list.append(date)
    #
    # from collections import Counter
    # append_date_month_by_counter = Counter(append_date_month_list)
    # append_date_month_by_counter_list = sorted(append_date_month_by_counter.items(), key=lambda x: x[0])
    # for date, counter in append_date_month_by_counter_list:
    #     print(date, counter)
    #
    # append_date_month_list = [x[0] for x in append_date_month_by_counter_list]
    # counter_list = [x[1] for x in append_date_month_by_counter_list]
    #
    # import matplotlib.pyplot as plt
    #
    # fig = plt.figure(1)
    # fig.suptitle('Price of games', fontsize=14, fontweight='bold')
    # ax = fig.add_subplot(111)
    #
    # ax.plot(append_date_month_list, counter_list, label='Games')
    #
    # ax.legend()
    # ax.grid()
    # ax.set_title('Append date')
    # ax.set_xlabel('Date')
    # ax.set_ylabel('Count')
    #
    # plt.gcf().autofmt_xdate()
    #
    # plt.show()
