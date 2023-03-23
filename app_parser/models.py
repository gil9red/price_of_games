#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from dataclasses import dataclass


@dataclass
class Game:
    name: str
    platform: str
    kind: str


@dataclass
class Genre:
    id: int
    name: str
    description: str


@dataclass
class GameInfo(Game):
    id: int
    price: int | None
    append_date: str
    append_date_timestamp: int
    genres: list[str]


@dataclass
class PriceUpdateResult:
    game_ids: list[int]
    game_name: str
    price: int | None


@dataclass
class RenameGameResult:
    game_ids_with_changed_name: list[int]
    game_ids_with_changed_price: list[int]
    new_name: str
    price: int | None
