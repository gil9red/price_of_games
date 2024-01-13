#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from db import Game


hour_by_number: dict[int, int] = {i: 0 for i in range(24)}
for game in Game.select():
    hour = game.append_date.hour
    hour_by_number[hour] += 1

for hour, number in sorted(hour_by_number.items(), key=lambda x: x[1], reverse=True):
    print(f"{hour}: {number}")
"""
23: 184
1: 168
2: 168
0: 153
22: 137
3: 129
20: 125
4: 76
21: 72
19: 65
16: 57
7: 51
8: 49
5: 46
13: 41
14: 41
15: 41
9: 40
17: 39
18: 38
6: 34
11: 33
10: 31
12: 23
"""
