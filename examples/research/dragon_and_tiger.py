# -*- coding: utf-8 -*-
from zvt.api.selector import get_big_players, get_player_success_rate
from zvt.domain import DragonAndTiger

if __name__ == "__main__":
    provider = "em`"
    DragonAndTiger.record_data(provider=provider)
    players = get_big_players()
    df = get_player_success_rate(start_timestamp="2019-01-01", intervals=[3, 8, 30, 90], players=players)
    print(df)
