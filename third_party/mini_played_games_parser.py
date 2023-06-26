#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


FINISHED_GAME = 'FINISHED_GAME'
NOT_FINISHED_GAME = 'NOT_FINISHED_GAME'
FINISHED_WATCHED = 'FINISHED_WATCHED'
NOT_FINISHED_WATCHED = 'NOT_FINISHED_WATCHED'


def is_finished(category: str) -> bool:
    return category in (FINISHED_GAME, FINISHED_WATCHED)


def is_gamed(category: str) -> bool:
    return category in (NOT_FINISHED_GAME, FINISHED_GAME)


def is_watched(category: str) -> bool:
    return category in (NOT_FINISHED_WATCHED, FINISHED_WATCHED)


def parse_played_games(text: str, silence: bool=False) -> dict:
    """
    Функция для парсинга списка игр.

    """

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


if __name__ == '__main__':
    def print_text(text, export_to_file_name):
        platforms = parse_played_games(text)
        print('Platforms:', len(platforms))

        total_games = 0
        for categories in platforms.values():
            for games in categories.values():
                total_games += len(games)

        print('Games:', total_games)
        print()
        print(', '.join(platforms.keys()))
        print(platforms)

        import json
        json.dump(platforms, open(export_to_file_name, mode='w', encoding='utf-8'), ensure_ascii=False, indent=4)

    def get_text_from_local():
        with open('gistfile1.txt', encoding='utf-8') as f:
            return f.read()

    def get_text_from_url():
        url_gist = 'https://gist.github.com/gil9red/2f80a34fb601cd685353'

        import requests
        rs = requests.get(url_gist)

        import re
        match = re.search('/gil9red/2f80a34fb601cd685353/raw/.+/gistfile1.txt', rs.text)
        if not match:
            return

        from urllib.parse import urljoin
        url = urljoin(rs.url, match.group())

        rs = requests.get(url)
        return rs.text

    print('get_text_from_local')
    text = get_text_from_local()
    print_text(text, 'games_local.json')

    print('\n')
    print('get_text_from_url')
    text = get_text_from_url()
    print_text(text, 'games_url.json')
