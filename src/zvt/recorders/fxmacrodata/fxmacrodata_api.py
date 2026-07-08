# -*- coding: utf-8 -*-
import os

import pandas as pd
import requests

from zvt.api.kdata import generate_kdata_id
from zvt.contract import Exchange, IntervalLevel, TradableType
from zvt.contract.api import decode_entity_id
from zvt.utils.time_utils import to_pd_timestamp

PROVIDER = "fxmacrodata"
FXMACRODATA_API_BASE_URL = "https://fxmacrodata.com/api/v1"
FXMACRODATA_API_KEY_ENV_VARS = ("FXMACRODATA_API_KEY", "FXMD_API_KEY")
FXMACRODATA_DEFAULT_CURRENCY_PAIRS = [
    "AUDUSD",
    "BRLUSD",
    "CADUSD",
    "CHFUSD",
    "CNHUSD",
    "CNYUSD",
    "DKKUSD",
    "EURUSD",
    "GBPUSD",
    "IDRUSD",
    "ILSUSD",
    "JPYUSD",
    "NGNUSD",
    "NOKUSD",
    "NZDUSD",
    "PENUSD",
    "SEKUSD",
    "THBUSD",
]


def to_currency_entity_id(code):
    return f"{TradableType.currency.value}_{Exchange.forex.value}_{normalize_currency_pair(code)}"


def normalize_currency_pair(code):
    normalized = "".join(char for char in str(code).upper() if char.isalpha())
    if len(normalized) != 6:
        raise ValueError("currency pair must look like EURUSD or EUR/USD")
    return normalized


def get_currency_list(codes=None):
    if codes is None:
        codes = FXMACRODATA_DEFAULT_CURRENCY_PAIRS

    rows = []
    for raw_code in codes:
        code = normalize_currency_pair(raw_code)
        entity_id = to_currency_entity_id(code)
        rows.append(
            {
                "id": entity_id,
                "entity_id": entity_id,
                "entity_type": TradableType.currency.value,
                "exchange": Exchange.forex.value,
                "code": code,
                "name": code,
            }
        )

    return pd.DataFrame.from_records(rows)


def get_kdata(
    entity_id,
    session=None,
    start_timestamp=None,
    end_timestamp=None,
    api_key=None,
    base_url=FXMACRODATA_API_BASE_URL,
    timeout=30,
):
    entity_type, _, code = decode_entity_id(entity_id)
    if entity_type != TradableType.currency.value:
        raise ValueError(f"FXMacroData only supports currency entities, got {entity_id}")

    code = normalize_currency_pair(code)
    base_currency = code[:3].lower()
    quote_currency = code[3:].lower()
    params = _query_params(start_timestamp, end_timestamp, api_key)
    url = f"{base_url.rstrip('/')}/forex/{base_currency}/{quote_currency}"

    http = session or requests
    response = http.get(
        url,
        params=params,
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    close_response(response)

    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("FXMacroData response did not include a data list")

    kdatas = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        date_value = row.get("date")
        price_value = row.get("val")
        if date_value is None or price_value is None:
            continue
        timestamp = to_pd_timestamp(date_value)
        price = float(price_value)
        kdatas.append(
            {
                "id": generate_kdata_id(
                    entity_id=entity_id,
                    timestamp=timestamp,
                    level=IntervalLevel.LEVEL_1DAY,
                ),
                "timestamp": timestamp,
                "entity_id": entity_id,
                "provider": PROVIDER,
                "code": code,
                "name": code,
                "level": IntervalLevel.LEVEL_1DAY.value,
                "open": price,
                "close": price,
                "high": price,
                "low": price,
                "volume": 0.0,
                "turnover": 0.0,
                "turnover_rate": 0.0,
            }
        )

    if kdatas:
        return pd.DataFrame.from_records(kdatas).sort_values("timestamp")


def close_response(response):
    close = getattr(response, "close", None)
    if close:
        close()


def _query_params(start_timestamp, end_timestamp, api_key):
    params = {}
    if start_timestamp is not None:
        params["start_date"] = _date_param(start_timestamp)
    if end_timestamp is not None:
        params["end_date"] = _date_param(end_timestamp)

    api_key = api_key or _api_key_from_environment()
    if api_key:
        params["api_key"] = api_key

    return params


def _date_param(value):
    return to_pd_timestamp(value).date().isoformat()


def _api_key_from_environment():
    for env_var in FXMACRODATA_API_KEY_ENV_VARS:
        api_key = os.getenv(env_var)
        if api_key:
            return api_key
    return None


__all__ = [
    "PROVIDER",
    "FXMACRODATA_API_BASE_URL",
    "FXMACRODATA_DEFAULT_CURRENCY_PAIRS",
    "get_currency_list",
    "get_kdata",
    "normalize_currency_pair",
    "to_currency_entity_id",
]
