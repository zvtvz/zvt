# -*- coding: utf-8 -*-
import pandas as pd

from zvt.recorders.fxmacrodata import fxmacrodata_api


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.closed = False

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(
            {
                "url": url,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return self.response


def test_get_currency_list():
    df = fxmacrodata_api.get_currency_list(codes=["eur/usd"])

    assert df.to_dict("records") == [
        {
            "id": "currency_forex_EURUSD",
            "entity_id": "currency_forex_EURUSD",
            "entity_type": "currency",
            "exchange": "forex",
            "code": "EURUSD",
            "name": "EURUSD",
        }
    ]


def test_get_kdata_fetches_fxmacrodata_prices():
    response = FakeResponse(
        {
            "data": [
                {"date": "2024-01-03", "val": 1.092},
                {"date": "2024-01-01", "val": "1.1038"},
            ]
        }
    )
    session = FakeSession(response=response)

    df = fxmacrodata_api.get_kdata(
        entity_id="currency_forex_EURUSD",
        session=session,
        start_timestamp="2024-01-01",
        end_timestamp="2024-01-31",
        api_key="test-key",
        timeout=12,
    )

    assert session.calls == [
        {
            "url": "https://fxmacrodata.com/api/v1/forex/eur/usd",
            "params": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "api_key": "test-key",
            },
            "headers": {"Accept": "application/json"},
            "timeout": 12,
        }
    ]
    assert response.closed
    assert df["id"].tolist() == [
        "currency_forex_EURUSD_2024-01-01",
        "currency_forex_EURUSD_2024-01-03",
    ]
    assert df["provider"].tolist() == ["fxmacrodata", "fxmacrodata"]
    assert df["level"].tolist() == ["1d", "1d"]
    assert df["code"].tolist() == ["EURUSD", "EURUSD"]
    assert df["open"].tolist() == [1.1038, 1.092]
    assert df["high"].tolist() == [1.1038, 1.092]
    assert df["low"].tolist() == [1.1038, 1.092]
    assert df["close"].tolist() == [1.1038, 1.092]
    assert df["volume"].tolist() == [0.0, 0.0]
    assert df["timestamp"].tolist() == [
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-03"),
    ]
