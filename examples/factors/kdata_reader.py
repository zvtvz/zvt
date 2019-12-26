# -*- coding: utf-8 -*-
import time

import pandas as pd

from zvt.domain import *
from zvt.reader import *

r = DataReader(data_schema=CoinTickKdata, provider='ccxt', level='tick')


class CoinTickListener(DataListener):

    def on_data_loaded(self, data: pd.DataFrame) -> object:
        print(data)

    def on_data_changed(self, data: pd.DataFrame) -> object:
        pass

    def on_entity_data_changed(self, entity: str, added_data: pd.DataFrame) -> object:
        print(added_data)


r.register_data_listener(CoinTickListener())

while True:
    r.move_on()
    time.sleep(2)
