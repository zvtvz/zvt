import pandas as pd

from zvt.accounts.ccxt_account import CCXTAccount
from zvt.api.technical import init_securities
from zvt.domain import Provider, COIN_EXCHANGES, COIN_PAIRS, SecurityType
from zvt.domain.coin_meta import Coin
from zvt.recorders.recorder import Recorder


class CoinMetaRecorder(Recorder):
    provider = Provider.CCXT
    data_schema = Coin

    def __init__(self, batch_size=10, force_update=False, sleeping_time=10, exchanges=COIN_EXCHANGES) -> None:
        super().__init__(batch_size, force_update, sleeping_time)
        self.exchanges = COIN_EXCHANGES

    def run(self):
        for exchange_str in self.exchanges:
            exchange = CCXTAccount.get_ccxt_exchange(exchange_str)
            try:
                markets = exchange.fetch_markets()
                df = pd.DataFrame()

                # markets有些为key=symbol的dict,有些为list
                markets_type = type(markets)
                if markets_type != dict and markets_type != list:
                    self.logger.exception("unknown return markets type {}".format(markets_type))
                    return

                aa = []
                for market in markets:
                    if markets_type == dict:
                        name = market
                        code = market

                    if markets_type == list:
                        code = market['symbol']
                        name = market['symbol']

                    if name not in COIN_PAIRS:
                        continue
                    aa.append(market)

                    security_item = {
                        'id': '{}_{}_{}'.format(SecurityType.coin.value, exchange_str, code),
                        'exchange': exchange_str,
                        'type': SecurityType.coin.value,
                        'code': code,
                        'name': name
                    }

                    df = df.append(security_item, ignore_index=True)

                # 存储该交易所的数字货币列表
                if not df.empty:
                    init_securities(df=df, security_type=SecurityType.coin, provider=self.provider)
                self.logger.info("init_markets for {} success".format(exchange_str))
            except Exception as e:
                self.logger.exception("init_markets for {} failed".format(exchange_str), e)


if __name__ == '__main__':
    CoinMetaRecorder().run()
