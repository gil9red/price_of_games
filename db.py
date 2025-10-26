#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import enum
import logging
import time
import shutil

from datetime import datetime
from typing import Any, Callable, Type, Iterable, Optional, TypeVar

# pip install peewee
from peewee import (
    Model,
    TextField,
    ForeignKeyField,
    DateTimeField,
    BooleanField,
    CharField,
    IntegerField,
    fn,
)
from playhouse.shortcuts import model_to_dict
from playhouse.sqliteq import SqliteQueueDatabase

from config import BACKUP_DIR_LIST, DB_FILE_NAME, DB_DIR_NAME
from third_party.db_peewee_meta_model import MetaModel
from third_party.ttl_cache import ttl_cache


class NotDefinedParameterException(Exception):
    def __init__(self, parameter_name: str):
        self.parameter_name = parameter_name
        text = f'Parameter "{self.parameter_name}" must be defined!'

        super().__init__(text)


class ResultEnum(enum.Enum):
    ADDED = enum.auto()
    UPDATED = enum.auto()
    NOTHING = enum.auto()
    DELETED = enum.auto()


def db_create_backup(log: logging.Logger):
    for path in BACKUP_DIR_LIST:
        zip_name = path / f"{datetime.today().date()}.sqlite"

        log.info(f"Создание бэкапа базы данных в: {zip_name}")
        shutil.make_archive(zip_name, "zip", DB_DIR_NAME)


# This working with multithreading
# SOURCE: http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#sqliteq
db = SqliteQueueDatabase(
    DB_FILE_NAME,
    pragmas={
        "foreign_keys": 1,
        "journal_mode": "wal",  # WAL-mode
        "cache_size": -1024 * 64,  # 64MB page-cache
    },
    use_gevent=False,  # Use the standard library "threading" module.
    autostart=True,
    queue_max_size=64,  # Max. # of pending writes that can accumulate.
    results_timeout=5.0,  # Max. time to wait for query to be executed.
)


def create_trigger_before_delete(
    in_table: Type[Model],
    for_table_column_name: str,
    delete_from_table: Type[Model],
    delete_from_table_column_name: str
):
    def get_table_db_name(model: Type[Model]) -> str:
        return model._meta.name

    in_table_name = get_table_db_name(in_table)
    delete_from_table_name = get_table_db_name(delete_from_table)
    name = f"trigger_{in_table_name}__delete_{delete_from_table_name}"

    sql = f"""
    CREATE TRIGGER IF NOT EXISTS {name}
        BEFORE DELETE
            ON {in_table_name}
        FOR EACH ROW
    BEGIN 
        DELETE FROM {delete_from_table_name}
              WHERE {delete_from_table_column_name} = old.{for_table_column_name};
    END;
    """
    db.execute_sql(sql)


ChildModel = TypeVar("ChildModel", bound="BaseModel")


class BaseModel(MetaModel):
    class Meta:
        database = db


class Platform(BaseModel):
    name = TextField(unique=True)

    @classmethod
    def add(cls, name: str) -> "Platform":
        obj = cls.get_or_none(name=name)
        if not obj:
            obj = cls.create(name=name)
        return obj


class Genre(BaseModel):
    name = TextField(unique=True)
    description = TextField()
    aliases = TextField(default="")

    # TODO: Немного неэффективно, но пока так
    # TODO: Можно попробовать в BaseModel перекрыть методы типа get_by_id и get_or_none, добавив кэширование
    #       Возможно, peewee внутри по другому работает с методами
    @classmethod
    @ttl_cache(ttl_seconds=5 * 60)
    def get_from_cache(cls, genre_id: int) -> "Genre":
        return cls.get_by_id(genre_id)

    @classmethod
    def get_by(cls, name: str) -> Optional["Genre"]:
        if not name or not name.strip():
            raise NotDefinedParameterException(parameter_name="name")

        return cls.get_or_none(name=name)

    @classmethod
    def add_or_update(
        cls,
        name: str,
        description: str,
        aliases: str = "",
    ) -> tuple[ResultEnum, "Genre"]:
        obj = cls.get_by(name)
        if not obj:
            obj = cls.create(
                name=name,
                description=description,
            )
            return ResultEnum.ADDED, obj

        has_updated = False
        if obj.description != description:
            obj.description = description
            has_updated = True

        if aliases and obj.aliases != aliases:
            obj.aliases = aliases
            has_updated = True

        if has_updated:
            obj.save()
            return ResultEnum.UPDATED, obj

        return ResultEnum.NOTHING, obj


class Game(BaseModel):
    name = TextField()
    platform = ForeignKeyField(Platform, backref="games")
    kind = TextField()
    price = IntegerField(null=True)
    append_date = DateTimeField(default=datetime.now)
    modify_price_date = DateTimeField(default=datetime.now)
    has_checked_price = BooleanField(default=False)

    class Meta:
        indexes = (
            (("name", "platform", "kind"), True),
        )

    @classmethod
    def get_by(cls, name: str, platform: Platform, kind: str) -> Optional["Game"]:
        if not name or not name.strip():
            raise NotDefinedParameterException(parameter_name="name")

        if not platform:
            raise NotDefinedParameterException(parameter_name="platform")

        if not kind or not kind.strip():
            raise NotDefinedParameterException(parameter_name="kind")

        return cls.get_or_none(name=name, platform=platform, kind=kind)

    @classmethod
    def add(cls, name: str, platform: Platform, kind: str) -> "Game":
        obj = cls.get_by(name, platform, kind)
        if not obj:
            obj = cls.create(
                name=name,
                platform=platform,
                kind=kind,
            )

        return obj

    def set_price(self, value: int):
        self.price = value
        self.modify_price_date = datetime.now()
        self.save()

    def add_genre(self, genre: str | Genre) -> tuple[ResultEnum, Genre]:
        if isinstance(genre, str):
            genre = Genre.get_by(genre)
            if not genre:
                raise Exception(f"Неизвестный жанр {genre!r}!")

        if genre in self.get_genres():
            return ResultEnum.NOTHING, genre

        Game2Genre.create(game=self, genre=genre)
        return ResultEnum.ADDED, genre

    def get_genres(self) -> list[Genre]:
        items: list[Genre] = [
            Genre.get_from_cache(link.genre_id)
            for link in self.links_to_genres.select(Game2Genre.genre_id)
        ]
        items.sort(key=lambda x: x.name)
        return items

    def set_genres(self, genres: list[str]) -> dict[ResultEnum, int]:
        result = {
            ResultEnum.ADDED: 0,
            ResultEnum.DELETED: 0,
            ResultEnum.NOTHING: 0,
        }

        genres: list[Genre] = [Genre.get_by(name) for name in genres]
        current_genres: list[Genre] = [link.genre for link in self.links_to_genres]

        # Если игры есть жанры, которых нет среди тех, что были переданы
        to_deleted = []
        for link in self.links_to_genres:
            if link.genre in genres:
                result[ResultEnum.NOTHING] += 1
            else:
                to_deleted.append(link)

        for link in to_deleted:
            link.delete_instance()

        result[ResultEnum.DELETED] = len(to_deleted)

        # Если у игры нет жанра из тех, что были переданы
        for genre in genres:
            if genre not in current_genres:
                result[ResultEnum.ADDED] += 1
                self.add_genre(genre)

        return result

    @classmethod
    def get_games_without_genres(cls) -> list["Game"]:
        sub_query = Game2Genre.select().where(Game2Genre.game == cls.id)
        query = cls.select().where(~fn.EXISTS(sub_query))
        return list(query)


class Game2Genre(BaseModel):
    game = ForeignKeyField(Game, backref="links_to_genres")
    genre = ForeignKeyField(Genre, backref="links_to_games")

    class Meta:
        indexes = (
            (("game", "genre"), True),
        )


class Settings(BaseModel):
    key = TextField(primary_key=True)
    value = TextField()

    @classmethod
    def set_value(cls, key: str, value: Any):
        obj = cls.get_or_none(key=key)
        if obj:
            if cls.get_value(key) != value:
                obj.value = value
                obj.save()
        else:
            cls.create(
                key=key,
                value=value,
            )

    @classmethod
    def get_value(
        cls,
        key: str,
        get_typing_value_func: Callable = None,
    ) -> str | Any | None:
        obj = cls.get_or_none(key=key)
        value = obj and obj.value

        if get_typing_value_func:
            value = get_typing_value_func(value)

        return value

    @classmethod
    def remove_value(cls, key: str):
        obj = cls.get_or_none(key=key)
        if obj:
            obj.delete_instance()


db.connect()
db.create_tables(BaseModel.get_inherited_models())

# Создание триггеров для автоматического удаления из Game2Genre
create_trigger_before_delete(Game, "id", Game2Genre, "game_id")
create_trigger_before_delete(Genre, "id", Game2Genre, "genre_id")

# Задержка в 50мс, чтобы дать время на запуск SqliteQueueDatabase и создание таблиц
# Т.к. в SqliteQueueDatabase запросы на чтение выполняются сразу, а на запись попадают в очередь
time.sleep(0.050)


if __name__ == "__main__":
    BaseModel.print_count_of_tables()
    # Game: 1689, Game2Genre: 6973, Genre: 78, Platform: 24, Settings: 1
    print()

    # print(Settings.get_value('last_run_date'))
    # print()
    #
    # print('Last 5:')
    # for game in Game.select().order_by(Game.id.desc()).limit(5):
    #     print(game)
