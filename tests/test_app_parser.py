#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest

from inspect import cleandoc
from unittest import TestCase
from unittest.mock import patch

import requests
from requests import Response

# TODO: Тестирование других модулей из app_parser/

from price_of_games.app_parser.utils import Game, smart_comparing_names, get_games
from price_of_games.common import (
    FINISHED_GAME,
    FINISHED_WATCHED,
    NOT_FINISHED_GAME,
    NOT_FINISHED_WATCHED,
)
from price_of_games.third_party.mini_played_games_parser import parse_played_games


def create_patch_requests_send(file_text: str):
    def patched_requests_send(request, **kwargs) -> Response:
        if request.url == "https://gist.github.com/gil9red/2f80a34fb601cd685353":
            content: bytes = b"""
                <html>
                    <div class="file-actions">
                        <a href="foo-bar" />
                    </div> 
                </html>
            """
        else:
            content: bytes = cleandoc(file_text).encode("utf-8")

        rs = Response()
        rs.status_code = 200
        rs._content = content
        rs.url = request.url
        rs.encoding = "utf-8"
        rs.request = request

        return rs

    return patched_requests_send


class TestCaseUtils(TestCase):
    def test_smart_comparing_names(self) -> None:
        for name_1, name_2 in [
            ("Half-Life 2", "Half-Life 2"),
            ("Alone in the Dark: Illumination", " Alone in the dark  ILLUMINATION"),
            ("Abzû", "ABZU"),
            ("Death Must Die", "Death Must Die v0.7"),
            ("Magic Rune Stone v0.9.20", "Magic Rune Stone"),
            ("Final Fantasy XV: Ardyn (DLC)", "Final Fantasy XV: Ardyn"),
            ("Silent Hill: Alchemilla (MOD)", "Silent Hill: Alchemilla"),
            ("Final Fantasy III (Remake)", "Final Fantasy III (Pixel Remaster)"),
            ("Final Fantasy III (Remake)", "Final Fantasy III"),
            ("Final Fantasy III (Pixel Remaster)", "Final Fantasy III"),
            ("Alone in the Dark (2008)", "Alone in the Dark (2024)"),
            ("Alone in the Dark (2008)", "Alone in the Dark"),
            (
                "Nightmares from the Deep: The Cursed Heart (Collector's Edition)",
                "Nightmares from the Deep: The Cursed Heart",
            ),
            (
                "Nightmares from the Deep: The Cursed Heart (Коллекционное издание)",
                "Nightmares from the Deep: The Cursed Heart",
            ),
            ("Divinity: Original Sin - Enhanced Edition", "Divinity: Original Sin"),
            (
                "Divinity: Original Sin 2 - Definitive Edition",
                "Divinity: Original Sin 2",
            ),
            ("DUSK '82: ULTIMATE EDITION", "DUSK '82"),
            ("Mass Effect: Legendary Edition", "Mass Effect"),
            (
                "Mass Effect 2: Legendary Edition - Genesis (DLC)",
                "Mass Effect 2: Genesis",
            ),
            ("Icewind Dale: Enhanced Edition", "Icewind Dale"),
            (
                "Icewind Dale: Enhanced Edition - Heart of Winter (DLC)",
                "Icewind Dale - Heart of Winter",
            ),
            (
                "The Secret of Monkey Island: Special Edition",
                "The Secret of Monkey Island",
            ),
            (
                "Monkey Island 2 Special Edition: LeChuck's Revenge",
                "Monkey Island 2: LeChuck's Revenge",
            ),
            ("Doom 3: BFG Edition", "Doom 3"),
            ("Killer is Dead: Nightmare Edition", "Killer is Dead"),
            ("Titan Quest Anniversary Edition", "Titan Quest"),
            (
                "Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
                "Нашёптанные секреты: Маскарад отравителя",
            ),
            ("Breath of Fire III", "Breath of Fire 3"),
            ("Breath of Fire 3", "Breath of Fire III"),
            ("Final Fantasy 9", "Final Fantasy IX"),
            ("Final Fantasy XV", "Final Fantasy 15"),
            ("Might and Magic: Heroes VI", "Might & Magic: Heroes VI"),
            (
                "NieR Replicant ver.1.22474487139...",
                "NieR Replicant ver.1.22474487139...",
            ),
            (
                "Titan Quest: The Immortal Throne (DLC)",
                "The Titan Quest: The Immortal Throne (DLC)",
            ),
            (
                "Titan Quest: The Immortal Throne, The (DLC)",
                "Titan Quest: The Immortal Throne (DLC)",
            ),
            (
                "The Titan Quest: The Immortal Throne (DLC)",
                "Titan Quest: The Immortal Throne, The (DLC)",
            ),
            (  # NOTE: Алгоритм убирает одно слово вместе со словом "Edition"
                "Frog Fractions: Game of the Decade Edition",
                "Frog Fractions: Game of the",
            ),
            (
                "Nightmares from the Deep 3: Davy Jones (Collector's Edition)",
                "Nightmares from the Deep 3: Davy Jones Collector's Edition",
            ),
            (
                "Nightmares from the Deep 3: Davy Jones (Collector’s Edition)",
                "Nightmares from the Deep 3: Davy Jones (Collector's Edition)",
            ),
            (
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition / Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition / Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
            ),
            (
                "Нашёптанные секреты: Маскарад отравителя Коллекционное издание / Whispered Secrets: Poisoner's Masquerade Collector's Edition",
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition / Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
            ),
            (
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition",
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition / Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
            ),
            (
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition",
                "Whispered Secrets: Poisoner's Masquerade / Нашёптанные секреты: Маскарад отравителя",
            ),
            (
                "Whispered Secrets: Poisoner's Masquerade",
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition / Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
            ),
            (
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition / Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
                "Whispered Secrets: Poisoner's Masquerade",
            ),
            (
                "Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition / Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
            ),
            (
                "Нашёптанные секреты: Маскарад отравителя",
                "Whispered Secrets: Poisoner's Masquerade / Нашёптанные секреты: Маскарад отравителя",
            ),
            (
                "Нашёптанные секреты: Маскарад отравителя",
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition / Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
            ),
            (
                "Whispered Secrets: Poisoner's Masquerade Collector's Edition / Нашёптанные секреты: Маскарад отравителя Коллекционное издание",
                "Нашёптанные секреты: Маскарад отравителя",
            ),
            (
                "Outlast: Whistleblower (DLC)",
                "Outlast: Whistleblower DLC",
            ),
        ]:
            with self.subTest(name_1=name_1, name_2=name_2):
                self.assertTrue(
                    smart_comparing_names(name_1, name_2),
                    f"{name_1!r} != {name_2!r}",
                )

    def test_smart_comparing_names_false(self) -> None:
        for name_1, name_2 in [
            ("Half-Life 2", "ABZU"),
            ("Alone in the Dark: Illumination", "Half-Life 2"),
            ("Abzû", "Alone in the dark  ILLUMINATION"),
        ]:
            with self.subTest(name_1=name_1, name_2=name_2):
                self.assertFalse(
                    smart_comparing_names(name_1, name_2),
                    f"{name_1!r} != {name_2!r}",
                )

    def test_get_games(self):
        sort_key_func = lambda obj: (obj.platform, obj.kind, obj.name)

        file_text: str = """
            PC:
            @-Hell is Us
              Russian Train Trip
            @ Russian Train Trip 2
            @-Russian Train Trip 3
            
            PS1:
              Spec Ops: Airborne Commando
            @ Spec Ops: Airborne Commando
        """
        expected_games: list[Game] = sorted(
            [
                Game(name="Russian Train Trip", platform="PC", kind=FINISHED_GAME),
                Game(
                    name="Russian Train Trip 2",
                    platform="PC",
                    kind=FINISHED_WATCHED,
                ),
                Game(
                    name="Russian Train Trip 3",
                    platform="PC",
                    kind=NOT_FINISHED_WATCHED,
                ),
                Game(name="Hell is Us", platform="PC", kind=NOT_FINISHED_WATCHED),
                Game(
                    name="Spec Ops: Airborne Commando",
                    platform="PS1",
                    kind=FINISHED_GAME,
                ),
                Game(
                    name="Spec Ops: Airborne Commando",
                    platform="PS1",
                    kind=FINISHED_WATCHED,
                ),
            ],
            key=sort_key_func,
        )

        with patch.object(
            requests.Session,
            attribute="send",
            side_effect=create_patch_requests_send(file_text),
        ):
            games = get_games()
            games.sort(key=sort_key_func)

            self.assertEqual(expected_games, games)


class TestCaseThirdParty(TestCase):
    def test_parse_played_games(self):
        text: str = """
            PC:
              Foo 1-3
            ? Bar
              Bar
              Bar
            - Bar
            @ Bar 2
            @-Bar 2
        """
        text = cleandoc(text)
        errors = []
        platforms = parse_played_games(text, silence=True, errors=errors)
        self.assertEqual(
            ["Foo", "Foo 2", "Foo 3", "Bar"],
            platforms["PC"][FINISHED_GAME],
        )
        self.assertEqual(["Bar"], platforms["PC"][NOT_FINISHED_GAME])
        self.assertEqual(["Bar 2"], platforms["PC"][FINISHED_WATCHED])
        self.assertEqual(["Bar 2"], platforms["PC"][NOT_FINISHED_WATCHED])
        self.assertEqual(
            [
                "Странный формат строки: '? Bar'",
                'Предотвращено добавление дубликата игры "Bar"',
                'Игра "Bar" (PC) присутствует и в не пройденных, и в пройденных',
                'Игра "Bar 2" (PC) присутствует и в не просмотренных, и в просмотренных',
            ],
            errors,
        )


if __name__ == "__main__":
    unittest.main()
