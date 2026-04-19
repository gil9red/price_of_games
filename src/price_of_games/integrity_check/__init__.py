#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from dataclasses import dataclass, field

from price_of_games import db
from price_of_games.app_parser.utils import get_games
from price_of_games.app_parser.models import Game
from price_of_games.common import FINISHED_GAME, FINISHED_WATCHED, get_logger
from price_of_games.third_party.add_notify_telegram import add_notify


log = get_logger(__name__)


@dataclass
class CheckInfo:
    games_from_web: list[Game]
    games_from_db: list[Game]

    # Поля, которые вычислятся автоматически
    missing_locally: list[Game] = field(init=False)
    extra_locally: list[Game] = field(init=False)
    is_consistent: bool = field(init=False)

    def __post_init__(self) -> None:
        self.missing_locally = [
            game for game in self.games_from_web if game not in self.games_from_db
        ]
        self.extra_locally = [
            game for game in self.games_from_db if game not in self.games_from_web
        ]
        self.is_consistent = not (self.missing_locally or self.extra_locally)

    def get_report(self) -> str:
        if self.is_consistent:
            return "✅ Данные синхронизированы."
        return (
            f"❌ Рассинхрон!\n"
            f"Отсутствует локально: {len(self.missing_locally)}\n"
            f"Лишних локально: {len(self.extra_locally)}"
        )


def integrity_check() -> CheckInfo:
    game_sort_key_func = lambda game: (game.platform, game.kind, game.name)

    games_from_web: list[Game] = [
        game for game in get_games() if game.kind in [FINISHED_GAME, FINISHED_WATCHED]
    ]
    games_from_web.sort(key=game_sort_key_func)

    games_from_db: list[Game] = [
        Game(name=game.name, kind=game.kind, platform=game.platform.name)
        for game in db.Game.select().where(
            db.Game.kind.in_([FINISHED_GAME, FINISHED_WATCHED])
        )
    ]
    games_from_db.sort(key=game_sort_key_func)

    return CheckInfo(games_from_web=games_from_web, games_from_db=games_from_db)


def run() -> None:
    def format_games(games: list[Game], limit: int = 15) -> str:
        items = [f"• {g.name} [{g.platform}] ({g.kind})" for g in games[:limit]]
        if len(games) > limit:
            items.append(f"... и еще {len(games) - limit} игр")

        return "\n".join(items)

    log.info("Запуск проверки целостности")

    check_info: CheckInfo = integrity_check()
    log.info(f"Целостность: {check_info.is_consistent}")

    report: str = check_info.get_report()
    log.info(report)

    if check_info.is_consistent:
        return

    lines: list[str] = [report]

    if check_info.missing_locally:
        lines.append("")
        lines.append(f"Отсутствующие:")
        lines.append(format_games(check_info.missing_locally))

    if check_info.extra_locally:
        lines.append("")
        lines.append(f"Лишние:")
        lines.append(format_games(check_info.extra_locally))

    text: str = "\n".join(lines).strip()

    log.info(f"Отправка уведомления:\n{text}")
    add_notify(name="Цены игр [Проверка целостности]", message=text)


if __name__ == "__main__":
    run()
