#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
import logging
import shutil

from typing import Any, Callable, Union, Optional

# pip install peewee
from peewee import (
    SqliteDatabase, Model, fn,
    TextField, ForeignKeyField, DateTimeField, BooleanField
)

from config import BACKUP_DIR_LIST, DB_FILE_NAME
from third_party.shorten import shorten


def db_create_backup(log: logging.Logger):
    for path in BACKUP_DIR_LIST:
        file_name = str(DT.datetime.today().date()) + '.sqlite'
        file_name = path / file_name

        log.debug(f'Doing create backup in: {file_name}')
        shutil.copy(DB_FILE_NAME, file_name)


# Ensure foreign-key constraints are enforced.
db = SqliteDatabase(DB_FILE_NAME, pragmas={'foreign_keys': 1})


class BaseModel(Model):
    class Meta:
        database = db

    def __str__(self):
        fields = []
        for k, field in self._meta.fields.items():
            v = getattr(self, k)

            if isinstance(field, TextField):
                if v:
                    v = repr(shorten(v))

            elif isinstance(field, ForeignKeyField):
                k = f'{k}_id'
                if v:
                    v = v.id

            fields.append(f'{k}={v}')

        return self.__class__.__name__ + '(' + ', '.join(fields) + ')'


class Game(BaseModel):
    name = TextField()
    price = TextField(null=True)  # TODO: как float / REAL
    append_date = DateTimeField(default=DT.datetime.now)
    modify_price_date = DateTimeField(default=DT.datetime.now)
    kind = TextField()
    check_steam = BooleanField(default=False)

    class Meta:
        indexes = (
            (("name", "kind"), True),
        )

    @property
    def append_date_dt(self) -> Union[DT.datetime, DateTimeField]:
        if isinstance(self.append_date, str):
            return DT.datetime.fromisoformat(self.append_date)

        return self.append_date

    @property
    def modify_price_date_dt(self) -> Union[DT.datetime, DateTimeField]:
        if isinstance(self.modify_price_date, str):
            return DT.datetime.fromisoformat(self.modify_price_date)

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
    def get_value(cls, key: str, get_typing_value_func: Callable = None) -> Optional[Union[str, Any]]:
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
db.create_tables([Game, Settings])


if __name__ == '__main__':
    print(Settings.get_value('last_run_date'))
    print()

    print('Last 5:')
    for game in Game.select().order_by(Game.id.desc()).limit(5):
        print(game)
