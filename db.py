#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import enum
import logging
import time
import shutil

from datetime import datetime
from typing import Any, Callable, Type, Iterable, Optional

# pip install peewee
from peewee import Model, TextField, ForeignKeyField, DateTimeField, BooleanField, CharField, IntegerField, fn
from playhouse.sqliteq import SqliteQueueDatabase

from config import BACKUP_DIR_LIST, DB_FILE_NAME, DB_DIR_NAME
from third_party.shorten import shorten


class NotDefinedParameterException(Exception):
    def __init__(self, parameter_name: str):
        self.parameter_name = parameter_name
        text = f'Parameter "{self.parameter_name}" must be defined!'

        super().__init__(text)


class ResultEnum(enum.Enum):
    ADDED = enum.auto()
    UPDATED = enum.auto()
    NOTHING = enum.auto()


def db_create_backup(log: logging.Logger):
    for path in BACKUP_DIR_LIST:
        zip_name = path / f'{datetime.today().date()}.sqlite'

        log.info(f'Создание бэкапа базы данных в: {zip_name}')
        shutil.make_archive(zip_name, 'zip', DB_DIR_NAME)


# This working with multithreading
# SOURCE: http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#sqliteq
db = SqliteQueueDatabase(
    DB_FILE_NAME,
    pragmas={
        'foreign_keys': 1,
        'journal_mode': 'wal',    # WAL-mode
        'cache_size': -1024 * 64  # 64MB page-cache
    },
    use_gevent=False,     # Use the standard library "threading" module.
    autostart=True,
    queue_max_size=64,    # Max. # of pending writes that can accumulate.
    results_timeout=5.0,  # Max. time to wait for query to be executed.
)


class BaseModel(Model):
    class Meta:
        database = db

    def get_new(self) -> Type['BaseModel']:
        return type(self).get(self._pk_expr())

    @classmethod
    def get_first(cls) -> Type['BaseModel']:
        return cls.select().first()

    @classmethod
    def get_last(cls) -> Type['BaseModel']:
        return cls.select().order_by(cls.id.desc()).first()

    @classmethod
    def get_inherited_models(cls) -> list[Type['BaseModel']]:
        return sorted(cls.__subclasses__(), key=lambda x: x.__name__)

    @classmethod
    def print_count_of_tables(cls):
        items = []
        for sub_cls in cls.get_inherited_models():
            name = sub_cls.__name__
            count = sub_cls.select().count()
            items.append(f'{name}: {count}')

        print(', '.join(items))

    @classmethod
    def count(cls, filters: Iterable = None) -> int:
        query = cls.select()
        if filters:
            query = query.filter(*filters)
        return query.count()

    def __str__(self):
        fields = []
        for k, field in self._meta.fields.items():
            v = getattr(self, k)

            if isinstance(field, (TextField, CharField)):
                if v:
                    v = repr(shorten(v))

            elif isinstance(field, ForeignKeyField):
                k = f'{k}_id'
                if v:
                    v = v.id

            fields.append(f'{k}={v}')

        return self.__class__.__name__ + '(' + ', '.join(fields) + ')'


class Platform(BaseModel):
    name = TextField(unique=True)

    @classmethod
    def add(cls, name: str) -> 'Platform':
        return cls.get_or_create(name=name)[0]


class Game(BaseModel):
    name = TextField()
    platform = ForeignKeyField(Platform, backref='games')
    kind = TextField()
    price = IntegerField(null=True)
    append_date = DateTimeField(default=datetime.now)
    modify_price_date = DateTimeField(default=datetime.now)
    has_checked_price = BooleanField(default=False)

    class Meta:
        indexes = (
            (("name", "platform", "kind"), True),
        )

    def set_price(self, value: int):
        self.price = value
        self.modify_price_date = datetime.now()
        self.save()

    @property
    def append_date_dt(self) -> datetime | DateTimeField:
        if isinstance(self.append_date, str):
            return datetime.fromisoformat(self.append_date)

        return self.append_date

    @property
    def modify_price_date_dt(self) -> datetime | DateTimeField:
        if isinstance(self.modify_price_date, str):
            return datetime.fromisoformat(self.modify_price_date)

        return self.modify_price_date

    def add_genre(self, genre_name: str) -> tuple[ResultEnum, 'Genre']:
        genre = Genre.get_by(genre_name)
        if not genre:
            raise Exception(f'Неизвестный жанр {genre_name!r}!')

        if genre in self.get_genres():
            return ResultEnum.NOTHING, genre

        Game2Genre.create(game=self, genre=genre)
        return ResultEnum.ADDED, genre

    def get_genres(self) -> list['Genre']:
        items: list[Genre] = [link.genre for link in self.links_to_genres]
        items.sort(key=lambda x: x.name)
        return items

    @classmethod
    def get_games_without_genres(cls) -> list['Game']:
        sub_query = Game2Genre.select().where(Game2Genre.game == cls.id)
        query = cls.select().where(~fn.EXISTS(sub_query))
        return list(query)


class Genre(BaseModel):
    name = TextField(unique=True)
    title = TextField()
    description = TextField()

    @classmethod
    def get_by(cls, name: str) -> Optional['Genre']:
        if not name or not name.strip():
            raise NotDefinedParameterException(parameter_name='name')

        return cls.get_or_none(name=name)

    @classmethod
    def add_or_update(cls, name: str, title: str, description: str) -> tuple[ResultEnum, 'Genre']:
        obj = cls.get_by(name)
        if not obj:
            obj = cls.create(
                name=name,
                title=title,
                description=description,
            )
            return ResultEnum.ADDED, obj

        if obj.title != title or obj.description != description:
            obj.title = title
            obj.description = description
            obj.save()
            return ResultEnum.UPDATED, obj

        return ResultEnum.NOTHING, obj


class Game2Genre(BaseModel):
    game = ForeignKeyField(Game, backref='links_to_genres')
    genre = ForeignKeyField(Genre, backref='links_to_games')

    class Meta:
        indexes = (
            (('game', 'genre'), True),
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
    def get_value(cls, key: str, get_typing_value_func: Callable = None) -> str | Any | None:
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

# Задержка в 50мс, чтобы дать время на запуск SqliteQueueDatabase и создание таблиц
# Т.к. в SqliteQueueDatabase запросы на чтение выполняются сразу, а на запись попадают в очередь
time.sleep(0.050)


if __name__ == '__main__':
    BaseModel.print_count_of_tables()
    # Game: 1689, Game2Genre: 6973, Genre: 78, Platform: 24, Settings: 1
    print()

    # print(Settings.get_value('last_run_date'))
    # print()
    #
    # print('Last 5:')
    # for game in Game.select().order_by(Game.id.desc()).limit(5):
    #     print(game)
