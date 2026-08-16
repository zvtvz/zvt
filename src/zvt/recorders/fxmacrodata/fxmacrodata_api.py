# -*- coding: utf-8 -*-
import os

import pandas as pd
import requests

from zvt.api.kdata import generate_kdata_id
from zvt.contract import Exchange, IntervalLevel, TradableType
from zvt.contract.api import decode_entity_id
from zvt.utils.time_utils import to_pd_timestamp

PROVIDER = "fxmacrodata"
FXMACRODATA_API_BASE_URL = "https://api.fxmacrodata.com/v1"
FXMACRODATA_PAGE_SIZE = 100
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
    if len(normalized) != 6 or not normalized.isascii():
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
    params.update({"limit": FXMACRODATA_PAGE_SIZE, "offset": 0})
    rows = []
    while True:
        try:
            response = http.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise RuntimeError("FXMacroData request failed") from exc
        try:
            if not response.ok:
                raise RuntimeError(
                    f"FXMacroData returned HTTP {response.status_code}"
                )
            try:
                payload = response.json()
            except ValueError as exc:
                raise ValueError("FXMacroData returned invalid JSON") from exc
        finally:
            close_response(response)

        page = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(page, list):
            raise ValueError("FXMacroData response did not include a data list")
        rows.extend(row for row in page if isinstance(row, dict))
        if len(page) < FXMACRODATA_PAGE_SIZE:
            break
        params["offset"] += FXMACRODATA_PAGE_SIZE

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
        open_value = float(row.get("open", price))
        high_value = float(row.get("high", price))
        low_value = float(row.get("low", price))
        close_value = float(row.get("close", price))
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
                "open": open_value,
                "close": close_value,
                "high": high_value,
                "low": low_value,
                "volume": 0.0,
                "turnover": 0.0,
                "turnover_rate": 0.0,
            }
        )

    if kdatas:
        return (
            pd.DataFrame.from_records(kdatas)
            .drop_duplicates(subset=["timestamp"], keep="first")
            .sort_values("timestamp")
            .reset_index(drop=True)
        )


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
