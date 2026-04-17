#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest
from unittest.mock import patch

import requests

from price_of_games import db

from price_of_games.app_parser.models import Game
from price_of_games.common import FINISHED_GAME, FINISHED_WATCHED
from price_of_games.integrity_check import CheckInfo, integrity_check

from tests.test_app_web import ATestCaseDb
from tests.test_app_parser import create_patch_requests_send


class TestCaseIntegrityCheck(ATestCaseDb):
    def test_integrity_check_ok(self) -> None:
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
        local_games: list[Game] = [
            Game(name="Russian Train Trip", platform="PC", kind=FINISHED_GAME),
            Game(name="Russian Train Trip 2", platform="PC", kind=FINISHED_WATCHED),
            Game(
                name="Spec Ops: Airborne Commando", platform="PS1", kind=FINISHED_GAME
            ),
            Game(
                name="Spec Ops: Airborne Commando",
                platform="PS1",
                kind=FINISHED_WATCHED,
            ),
        ]

        for game in local_games:
            db.Game.add(
                name=game.name,
                platform=db.Platform.add(game.platform),
                kind=game.kind,
            )

        with patch.object(
            requests.Session,
            attribute="send",
            side_effect=create_patch_requests_send(file_text),
        ):
            check_info: CheckInfo = integrity_check()
            self.assertTrue(check_info.is_consistent, "is_consistent is not True")
            self.assertEqual(
                [], check_info.missing_locally, "check_info.missing_locally"
            )
            self.assertEqual([], check_info.extra_locally, "check_info.extra_locally")

    def test_integrity_check_missing_locally(self) -> None:
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
        local_games: list[Game] = [
            Game(name="Russian Train Trip", platform="PC", kind=FINISHED_GAME),
            Game(
                name="Spec Ops: Airborne Commando",
                platform="PS1",
                kind=FINISHED_WATCHED,
            ),
        ]

        for game in local_games:
            db.Game.add(
                name=game.name,
                platform=db.Platform.add(game.platform),
                kind=game.kind,
            )

        with patch.object(
            requests.Session,
            attribute="send",
            side_effect=create_patch_requests_send(file_text),
        ):
            check_info: CheckInfo = integrity_check()
            self.assertFalse(check_info.is_consistent, "is_consistent is True")
            self.assertEqual(
                [
                    Game(
                        name="Russian Train Trip 2",
                        platform="PC",
                        kind=FINISHED_WATCHED,
                    ),
                    Game(
                        name="Spec Ops: Airborne Commando",
                        platform="PS1",
                        kind=FINISHED_GAME,
                    ),
                ],
                check_info.missing_locally,
                "check_info.missing_locally",
            )
            self.assertEqual(
                [],
                check_info.extra_locally,
                "check_info.extra_locally",
            )

    def test_integrity_check_extra_locally(self) -> None:
        file_text: str = """
            PC:
            @-Hell is Us
              Russian Train Trip
            @-Russian Train Trip 3
            
            PS1:
            @ Spec Ops: Airborne Commando
        """
        local_games: list[Game] = [
            Game(name="Russian Train Trip", platform="PC", kind=FINISHED_GAME),
            Game(name="Russian Train Trip 2", platform="PC", kind=FINISHED_WATCHED),
            Game(
                name="Spec Ops: Airborne Commando", platform="PS1", kind=FINISHED_GAME
            ),
            Game(
                name="Spec Ops: Airborne Commando",
                platform="PS1",
                kind=FINISHED_WATCHED,
            ),
        ]

        for game in local_games:
            db.Game.add(
                name=game.name,
                platform=db.Platform.add(game.platform),
                kind=game.kind,
            )

        with patch.object(
            requests.Session,
            attribute="send",
            side_effect=create_patch_requests_send(file_text),
        ):
            check_info: CheckInfo = integrity_check()
            self.assertFalse(check_info.is_consistent, "is_consistent is True")
            self.assertEqual(
                [],
                check_info.missing_locally,
                "check_info.missing_locally",
            )
            self.assertEqual(
                [
                    Game(
                        name="Russian Train Trip 2",
                        platform="PC",
                        kind=FINISHED_WATCHED,
                    ),
                    Game(
                        name="Spec Ops: Airborne Commando",
                        platform="PS1",
                        kind=FINISHED_GAME,
                    ),
                ],
                check_info.extra_locally,
                "check_info.extra_locally",
            )

    def test_integrity_check_missing_locally_and_extra_locally(self) -> None:
        file_text: str = """
            PC:
            @-Hell is Us
              Russian Train Trip
            @ Russian Train Trip 2
            @-Russian Train Trip 3
            
            PS1:
              Spec Ops: Airborne Commando
            @ Spec Ops: Airborne Commando
            
            PS2:
              Metal Gear Solid 3: Snake Eater
              
            PS3:
            @ Silent Hill: Downpour
        """
        local_games: list[Game] = [
            Game(name="Russian Train Trip", platform="PC", kind=FINISHED_GAME),
            Game(name="Russian Train Trip 2", platform="PC", kind=FINISHED_WATCHED),
            Game(
                name="Spec Ops: Airborne Commando", platform="PS1", kind=FINISHED_GAME
            ),
            Game(
                name="Spec Ops: Airborne Commando",
                platform="PS1",
                kind=FINISHED_WATCHED,
            ),
            Game(name="Final Fantasy IX", platform="PS1", kind=FINISHED_GAME),
        ]

        for game in local_games:
            db.Game.add(
                name=game.name,
                platform=db.Platform.add(game.platform),
                kind=game.kind,
            )

        with patch.object(
            requests.Session,
            attribute="send",
            side_effect=create_patch_requests_send(file_text),
        ):
            check_info: CheckInfo = integrity_check()
            self.assertFalse(check_info.is_consistent, "is_consistent is True")
            self.assertEqual(
                [
                    Game(
                        name="Metal Gear Solid 3: Snake Eater",
                        platform="PS2",
                        kind=FINISHED_GAME,
                    ),
                    Game(
                        name="Silent Hill: Downpour",
                        platform="PS3",
                        kind=FINISHED_WATCHED,
                    ),
                ],
                check_info.missing_locally,
                "check_info.missing_locally",
            )
            self.assertEqual(
                [Game(name="Final Fantasy IX", platform="PS1", kind=FINISHED_GAME)],
                check_info.extra_locally,
                "check_info.extra_locally",
            )


if __name__ == "__main__":
    unittest.main()
