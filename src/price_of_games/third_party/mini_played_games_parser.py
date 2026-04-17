#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re


# Регулярка вытаскивает выражения вида: 1, 2, 3 или 1-3, или римские цифры: III, IV
PARSE_GAME_NAME_PATTERN = re.compile(
    r"(\d+(, *?\d+)+)|(\d+ *?- *?\d+)|([MDCLXVI]+(, ?[MDCLXVI]+)+)",
    flags=re.IGNORECASE,
)

FINISHED_GAME = "FINISHED_GAME"
NOT_FINISHED_GAME = "NOT_FINISHED_GAME"
FINISHED_WATCHED = "FINISHED_WATCHED"
NOT_FINISHED_WATCHED = "NOT_FINISHED_WATCHED"

FLAG_BY_CATEGORY: dict[str, str] = {
    "  ": FINISHED_GAME,
    "- ": NOT_FINISHED_GAME,
    " -": NOT_FINISHED_GAME,
    " @": FINISHED_WATCHED,
    "@ ": FINISHED_WATCHED,
    "-@": NOT_FINISHED_WATCHED,
    "@-": NOT_FINISHED_WATCHED,
}


def parse_game_name(game_name: str) -> list[str]:
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
    if not match:
        return [game_name]

    seq_str = match.group(0)

    # "Resident Evil 4, 5, 6" -> "Resident Evil"
    # For not valid "Trollface Quest 1-7-8" -> "Trollface Quest"
    index = game_name.index(seq_str)
    base_name = game_name[:index].strip()

    seq_str = seq_str.replace(" ", "")

    if "," in seq_str:
        # '1,2,3' -> ['1', '2', '3']
        seq = seq_str.split(",")

    elif "-" in seq_str:
        seq = seq_str.split("-")

        # ['1', '7'] -> [1, 7]
        seq = list(map(int, seq))

        # [1, 7] -> ['1', '2', '3', '4', '5', '6', '7']
        seq = list(map(str, range(seq[0], seq[1] + 1)))

    else:
        return [game_name]

    # Сразу проверяем номер игры в серии и если она первая, то не добавляем в названии ее номер
    return [base_name if num == "1" else f"{base_name} {num}" for num in seq]


def parse_played_games(
    text: str,
    silence: bool = False,
    errors: list[str] | None = None,
) -> dict[str, dict[str, list[str]]]:
    """
    Функция для парсинга списка игр.

    """

    if errors is None:
        errors = []

    def _process_error(error_text: str):
        errors.append(error_text)
        if not silence:
            print(error_text)

    platforms: dict[str, dict[str, list[str]]] = dict()
    platform = None

    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue

        flag = line[:2]
        if flag not in FLAG_BY_CATEGORY and line.endswith(":"):
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
            _process_error(f"Странный формат строки: {line!r}")
            continue

        category = platform[category_name]

        game_name = line[2:]
        for game in parse_game_name(game_name):
            if game in category:
                _process_error(f'Предотвращено добавление дубликата игры "{game}"')
                continue

            category.append(game)

    # Проверка, что одна и та же игра не присутствует и в пройденных, и в не пройденных,
    # или в просмотренных и в не просмотренных
    for platform, categories in platforms.items():
        for game in categories[NOT_FINISHED_GAME]:
            if game in categories[FINISHED_GAME]:
                _process_error(
                    f'Игра "{game}" ({platform}) присутствует и в не пройденных, и в пройденных'
                )

        for game in categories[NOT_FINISHED_WATCHED]:
            if game in categories[FINISHED_WATCHED]:
                _process_error(
                    f'Игра "{game}" ({platform}) присутствует и в не просмотренных, и в просмотренных'
                )

    return platforms


if __name__ == "__main__":
    print("Tests")

    text = """
PC:
  Foo 1-3
? Bar
  Bar
  Bar
- Bar
@ Bar 2
@-Bar 2
    """.strip()
    errors = []
    platforms = parse_played_games(text, silence=True, errors=errors)
    assert platforms["PC"]["FINISHED_GAME"] == ["Foo", "Foo 2", "Foo 3", "Bar"]
    assert platforms["PC"]["NOT_FINISHED_GAME"] == ["Bar"]
    assert platforms["PC"]["FINISHED_WATCHED"] == ["Bar 2"]
    assert platforms["PC"]["NOT_FINISHED_WATCHED"] == ["Bar 2"]
    assert errors == [
        "Странный формат строки: '? Bar'",
        'Предотвращено добавление дубликата игры "Bar"',
        'Игра "Bar" (PC) присутствует и в не пройденных, и в пройденных',
        'Игра "Bar 2" (PC) присутствует и в не просмотренных, и в просмотренных',
    ]
