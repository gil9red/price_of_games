#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from dataclasses import dataclass
from typing import Optional


@dataclass
class Game:
    name: str
    platform: str
    kind: str


@dataclass
class GameInfo:
    id: int
    name: str
    kind: str
    platform: str
    price: Optional[int]
    append_date: str
    append_date_timestamp: int


@dataclass
class PriceUpdateResult:
    game_ids: list[int]
    game_name: str
    price: Optional[int]


@dataclass
class RenameGameResult:
    game_ids_with_changed_name: list[int]
    game_ids_with_changed_price: list[int]
    new_name: str
    price: Optional[int]
