#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest
from datetime import datetime

from peewee import SqliteDatabase

from common import FINISHED_GAME
from db import (
    NotDefinedParameterException,
    ResultEnum,
    BaseModel,
    Platform,
    Game,
    Genre,
    Game2Genre,
    Settings,
    db,
)
from app_web.lenta import (
    get_games,
    get_games_by_year,
    get_day_by_games,
    get_year_by_number,
    get_platforms,
)


# NOTE: https://docs.peewee-orm.com/en/latest/peewee/database.html#testing-peewee-applications
class ATestCaseDb(unittest.TestCase):
    def setUp(self):
        self.models = BaseModel.get_inherited_models()
        self.test_db = SqliteDatabase(":memory:")
        self.test_db.bind(self.models, bind_refs=False, bind_backrefs=False)
        self.test_db.connect()
        self.test_db.create_tables(self.models)

    def tearDown(self):
        db.bind(self.models, bind_refs=False, bind_backrefs=False)


class TestCaseDb(ATestCaseDb):
    def test_platform(self):
        with self.subTest("cls.count"):
            self.assertEqual(0, Platform.count())

        with self.subTest("cls.add"):
            name = "PC"
            platform = Platform.add(name)
            self.assertTrue(platform)
            self.assertEqual(name, platform.name)

            for _ in range(5):
                Platform.add(name)

            self.assertEqual(1, Platform.count())

            names = [name, "PS1", "PS2"]
            for name in names:
                Platform.add(name)

            self.assertEqual(len(names), Platform.count())

    def test_game(self):
        with self.subTest("cls.count"):
            self.assertEqual(0, Game.count())

        kind = FINISHED_GAME
        platform = Platform.add("PC")

        with self.subTest("cls.add"):
            name = "game1"

            game = Game.add(name, platform, kind)
            self.assertEqual(1, Game.count())
            self.assertEqual(name, game.name)
            self.assertEqual(platform, game.platform)
            self.assertEqual(kind, game.kind)

            for _ in range(5):
                Game.add(name, platform, kind)

            self.assertEqual(1, Game.count())

        with self.subTest("cls.get_by"):
            self.assertEqual(game, Game.get_by(game.name, game.platform, game.kind))

            self.assertIsNone(
                Game.get_by(game.name + game.name, game.platform, game.kind)
            )
            self.assertIsNone(
                Game.get_by(game.name, Platform.add("<UNKNOWN>"), game.kind + game.kind)
            )
            self.assertIsNone(
                Game.get_by(game.name, game.platform, game.kind + game.kind)
            )

            # Пустые параметры
            with self.assertRaises(NotDefinedParameterException):
                Game.get_by(name="", platform=platform, kind=kind)

            with self.assertRaises(NotDefinedParameterException):
                Game.get_by(name=None, platform=platform, kind=kind)

            with self.assertRaises(NotDefinedParameterException):
                Game.get_by(name="   ", platform=platform, kind=kind)

            with self.assertRaises(NotDefinedParameterException):
                Game.get_by(name=game.name, platform=None, kind=kind)

            with self.assertRaises(NotDefinedParameterException):
                Game.get_by(name=game.name, platform=platform, kind="")

            with self.assertRaises(NotDefinedParameterException):
                Game.get_by(name=game.name, platform=platform, kind=None)

            with self.assertRaises(NotDefinedParameterException):
                Game.get_by(name=game.name, platform=platform, kind="    ")

        with self.subTest("self.set_price"):
            self.assertIsNone(game.price)

            price = 999
            game.set_price(price)
            self.assertEqual(price, game.price)

        with self.subTest("self.append_date"):
            self.assertTrue(
                "append_date is not datetime", isinstance(game.append_date, datetime)
            )

        with self.subTest("self.modify_price_date"):
            self.assertTrue(
                "modify_price_date is not datetime",
                isinstance(game.modify_price_date, datetime),
            )

        genres = ["RPG", "Action", "Spy"]
        for name in genres:
            Genre.add_or_update(name=name, description="")

        with self.subTest("self.add_genre / self.get_genres"):
            self.assertEqual(0, len(game.get_genres()))
            for name in genres:
                game.add_genre(name)
            self.assertEqual(len(genres), len(game.get_genres()))

            # Несуществующий жанр
            with self.assertRaises(Exception):
                game.add_genre(genres[0] * 2)

            # Проверяем, что дубликаты не появятся
            for name in genres:
                game.add_genre(name)

            game.add_genre(Genre.get_by(genres[0]))

            self.assertEqual(len(genres), len(game.get_genres()))

        with self.subTest("self.set_genres"):
            game = Game.add(name="set_genres", platform=platform, kind=kind)

            result = game.set_genres([])
            self.assertEqual(
                {
                    ResultEnum.ADDED: 0,
                    ResultEnum.DELETED: 0,
                    ResultEnum.NOTHING: 0,
                },
                result,
            )
            self.assertEqual(0, len(game.get_genres()))

            result = game.set_genres(genres)
            self.assertEqual(
                {
                    ResultEnum.ADDED: 3,
                    ResultEnum.DELETED: 0,
                    ResultEnum.NOTHING: 0,
                },
                result,
            )
            self.assertEqual(3, len(game.get_genres()))

            result = game.set_genres(genres)
            self.assertEqual(
                {
                    ResultEnum.ADDED: 0,
                    ResultEnum.DELETED: 0,
                    ResultEnum.NOTHING: 3,
                },
                result,
            )
            self.assertEqual(3, len(game.get_genres()))

            result = game.set_genres(
                [genres[0], Genre.add_or_update(name="1234", description="")[1].name]
            )
            self.assertEqual(
                {
                    ResultEnum.ADDED: 1,
                    ResultEnum.DELETED: 2,
                    ResultEnum.NOTHING: 1,
                },
                result,
            )
            self.assertEqual(2, len(game.get_genres()))

        with self.subTest("cls.get_games_without_genres"):
            Game.truncate_table()
            Game2Genre.truncate_table()

            self.assertEqual(0, len(Game.get_games_without_genres()))

            items = []
            for i in range(5):
                items.append(Game.add(f"{name}_{i}", platform, kind))

            self.assertEqual(len(items), len(Game.get_games_without_genres()))

    def test_genre(self):
        with self.subTest("cls.count"):
            self.assertEqual(0, Genre.count())

        genres = ["RPG", "Action", "Spy"]

        with self.subTest("cls.get_by"):
            self.assertIsNone(Genre.get_by(name=genres[0]))

            # Пустые параметры
            with self.assertRaises(NotDefinedParameterException):
                Genre.get_by(name="")

            with self.assertRaises(NotDefinedParameterException):
                Genre.get_by(name=None)

            with self.assertRaises(NotDefinedParameterException):
                Genre.get_by(name="   ")

        with self.subTest("cls.add_or_update"):
            for name in genres:
                result, genre = Genre.add_or_update(name=name, description="")
                self.assertEqual(ResultEnum.ADDED, result)
                self.assertIsNotNone(genre)

                result, genre = Genre.add_or_update(name=name, description="")
                self.assertEqual(ResultEnum.NOTHING, result)
                self.assertIsNotNone(genre)

                result, genre = Genre.add_or_update(name=name, description=name)
                self.assertEqual(ResultEnum.UPDATED, result)
                self.assertIsNotNone(genre)

            self.assertEqual(len(genres), Genre.count())

            for name in genres:
                self.assertIsNotNone(Genre.get_by(name=name))
                self.assertEqual(name, Genre.get_by(name=name).name)

    def test_game2genre(self):
        with self.subTest("cls.count"):
            self.assertEqual(0, Game2Genre.count())

        genres = []
        for name in ["RPG", "Action", "Spy"]:
            _, genre = Genre.add_or_update(name=name, description="")
            genres.append(genre)

        kind = FINISHED_GAME
        platform = Platform.add("PC")
        games = [Game.add(f"game{i}", platform, kind) for i in range(3)]

        for game in games:
            for genre in genres:
                game.add_genre(genre)

        self.assertEqual(len(genres) * len(games), Game2Genre.count())

        with self.subTest("self.links_to_genres"):
            game = games[0]
            game_genres = [link.genre for link in game.links_to_genres]
            self.assertEqual(len(genres), len(game_genres))
            self.assertEqual(genres, game_genres)

        with self.subTest("self.links_to_games"):
            genre = genres[0]
            genre_games = [link.game for link in genre.links_to_games]
            self.assertEqual(len(games), len(genre_games))
            self.assertEqual(games, genre_games)

    def test_settings(self):
        with self.subTest("cls.count"):
            self.assertEqual(0, Settings.count())

        with self.subTest("cls.set_value / cls.get_value"):
            self.assertIsNone(Settings.get_value("abc"))

            Settings.set_value("abc", "123")
            self.assertEqual(1, Settings.count())

            Settings.set_value("abc", "123")
            self.assertEqual(1, Settings.count())

            self.assertEqual("123", Settings.get_value("abc"))
            self.assertEqual(123, Settings.get_value("abc", int))
            self.assertEqual(123, Settings.get_value("abc", get_typing_value_func=int))
            self.assertEqual(
                123, Settings.get_value("abc", get_typing_value_func=lambda x: int(x))
            )

            Settings.set_value("abc456", 456)
            self.assertEqual(2, Settings.count())
            self.assertEqual("456", Settings.get_value("abc456"))


class TestCaseDbLenta(ATestCaseDb):
    @staticmethod
    def create_games() -> list[Game]:
        kind = FINISHED_GAME
        platform = Platform.add("PC")
        games: list[Game] = [Game.add(f"game_{i}", platform, kind) for i in range(5)]
        games.sort(key=lambda obj: obj.append_date, reverse=True)

        return games

    def test_get_games(self):
        self.assertEqual(0, len(get_games()))

        games: list[Game] = self.create_games()
        actual: list[Game] = get_games()
        self.assertEqual(len(games), len(actual))
        self.assertEqual(games, actual)

    def test_get_games_by_year(self):
        year = datetime.now().year

        self.assertEqual(0, len(get_games_by_year(year)))

        games: list[Game] = self.create_games()
        actual: list[Game] = get_games_by_year(year)
        self.assertEqual(len(games), len(actual))
        self.assertEqual(games, actual)

        self.assertEqual(0, len(get_games_by_year(year - 1)))

    def test_get_day_by_games(self):
        now = datetime.now()
        year: int = now.year
        day: str = now.strftime("%d.%m.%Y")

        self.assertEqual(0, len(get_day_by_games(year)))

        games: list[Game] = self.create_games()
        actual: dict[str, list[Game]] = get_day_by_games(year)
        self.assertEqual({day: games}, actual)

    def test_get_year_by_number(self):
        year = datetime.now().year

        self.assertEqual(0, len(get_year_by_number()))

        games: list[Game] = self.create_games()
        actual: list[tuple[int, int]] = get_year_by_number()
        self.assertEqual([(year, len(games))], actual)

    def test_get_platforms(self):
        self.assertEqual(0, len(get_platforms()))

        items: list[str] = ["PS1", "PS2", "Android", "PC"]
        items.sort()

        for name in items:
            Platform.add(name)

        self.assertEqual(items, get_platforms())


if __name__ == "__main__":
    unittest.main()
