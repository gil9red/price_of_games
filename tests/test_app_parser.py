#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest

# TODO: Другие модули
from app_parser.utils import smart_comparing_names


class TestCaseUtils(unittest.TestCase):
    def test_smart_comparing_names(self):
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
        ]:
            with self.subTest(name_1=name_1, name_2=name_2):
                self.assertTrue(
                    smart_comparing_names(name_1, name_2),
                    f"{name_1!r} != {name_2!r}",
                )

    def test_smart_comparing_names_false(self):
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


if __name__ == "__main__":
    unittest.main()
