from datetime import datetime

import requests
from db import Game, Platform


rs = requests.get("http://127.0.0.1:10015/api/get_all_finished")
for game_data in rs.json():
    if game_data["platform"] == "PC":
        continue

    platform = Platform.get_or_none(Platform.name == game_data["platform"])
    if not platform:
        continue

    game = Game.get_or_none(
        Game.name == game_data["name"],
        Game.platform == platform,
        Game.kind == game_data["category"],
    )
    if not game:
        continue

    finish_datetime = datetime.fromisoformat(game_data["finish_datetime"])
    if game.append_date == finish_datetime:
        continue

    print(
        f"{game}\n    Update of append_date: {game.append_date} -> {finish_datetime}\n"
    )
    game.append_date = finish_datetime
    game.save()
