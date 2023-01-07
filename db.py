#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import logging
import shutil

from datetime import datetime
from typing import Any, Callable, Type, Iterable

# pip install peewee
from peewee import (
    SqliteDatabase, Model,
    TextField, ForeignKeyField, DateTimeField, BooleanField, CharField, IntegerField
)

from config import BACKUP_DIR_LIST, DB_FILE_NAME
from third_party.shorten import shorten


def db_create_backup(log: logging.Logger):
    for path in BACKUP_DIR_LIST:
        file_name = str(datetime.today().date()) + '.sqlite'
        file_name = path / file_name

        log.debug(f'Doing create backup in: {file_name}')
        shutil.copy(DB_FILE_NAME, file_name)


# Ensure foreign-key constraints are enforced.
db = SqliteDatabase(DB_FILE_NAME, pragmas={'foreign_keys': 1})


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


if __name__ == '__main__':
    BaseModel.print_count_of_tables()
    print()

    # print(Settings.get_value('last_run_date'))
    # print()
    #
    # print('Last 5:')
    # for game in Game.select().order_by(Game.id.desc()).limit(5):
    #     print(game)
