#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# import sqlite3
# connect = sqlite3.connect('gist_commits.sqlite')
#
# sqlite_text = 'SELECT committed_at, content FROM GistFile'
# for a, b in connect.execute(sqlite_text).fetchall():
#     if 'South Park: The Stick of Truth' in b:
#         print(a)


if __name__ == '__main__':
    price_by_date = dict()

    import glob
    for file_name in glob.glob('backup/*.sqlite'):
        import sqlite3
        connect = sqlite3.connect(file_name)

        sqlite_text = 'SELECT * FROM Game WHERE name = "South Park: The Stick of Truth"'
        rs = connect.execute(sqlite_text).fetchall()
        if rs:
            print(file_name)
            print(rs)
            # break

    #     sqlite_text = 'SELECT price FROM Game WHERE price is not null'
    #     price = sum(round(float(price.replace(',', '.'))) for (price,) in connect.execute(sqlite_text).fetchall())
    #
    #     if price not in price_by_date:
    #         price_by_date[price] = file_name.split('\\')[1].split('.')[0]
    #
    # print(price_by_date)
    #
    # # Данные для построения графика
    # x = list(sorted(price_by_date.keys()))
    #
    # from datetime import datetime
    # get_date = lambda date_str: datetime.strptime(date_str, '%Y-%m-%d')
    # y = list(get_date(price_by_date[key]) for key in sorted(price_by_date.keys()))
    #
    # import pylab
    # pylab.plot(x, y)
    #
    # pylab.xlabel('Price')
    # pylab.ylabel('Date')
    # pylab.grid()
    # pylab.show()
