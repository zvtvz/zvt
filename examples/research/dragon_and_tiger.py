# -*- coding: utf-8 -*-
from zvt.api.selector import get_big_players, get_player_success_rate
from zvt.domain import DragonAndTiger
from zvt.utils.time_utils import date_time_by_interval, current_date

if __name__ == "__main__":
    provider = "em"
    DragonAndTiger.record_data(provider=provider)
    end_timestamp = date_time_by_interval(current_date(), -60)
    # recent year
    start_timestamp = date_time_by_interval(end_timestamp, -400)
    print(f"{start_timestamp} to {end_timestamp}")
    players = get_big_players(start_timestamp=start_timestamp, end_timestamp=end_timestamp)
    print(players)
    df = get_player_success_rate(
        start_timestamp=start_timestamp, end_timestamp=end_timestamp, intervals=[3, 5, 10], players=players
    )
    print(df)
