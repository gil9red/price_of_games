#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from dataclasses import dataclass


@dataclass
class Game:
    name: str
    platform: str
    kind: str
