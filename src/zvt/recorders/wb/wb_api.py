# -*- coding: utf-8 -*-
import itertools
import re
from copy import copy

import pandas as pd
import requests

from zvt.contract.api import get_entity_code
from zvt.utils.pd_utils import normal_index_df
from zvt.utils.time_utils import to_pd_timestamp

WORLD_BANK_URL = "http://api.worldbank.org/v2"

# thanks to https://github.com/mwouts/world_bank_data

_economy_indicator_map = {
    "population": "SP.POP.TOTL",
    "gdp": "NY.GDP.MKTP.CD",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "gdp_per_employed": "SL.GDP.PCAP.EM.KD",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "agriculture_growth": "NV.AGR.TOTL.KD.ZG",
    "industry_growth": "NV.IND.TOTL.KD.ZG",
    "manufacturing_growth": "NV.IND.MANF.KD.ZG",
    "service_growth": "NV.SRV.TOTL.KD.ZG",
    "consumption_growth": "NE.CON.TOTL.KD.ZG",
    "capital_growth": "NE.GDI.TOTL.KD.ZG",
    "exports_growth": "NE.EXP.GNFS.KD.ZG",
    "imports_growth": "NE.IMP.GNFS.KD.ZG",
    "gni": "NY.GNP.ATLS.CD",
    "gni_per_capita": "NY.GNP.PCAP.CD",
    "gross_saving": "NY.GNS.ICTR.ZS",
    "cpi": "FP.CPI.TOTL",
    "unemployment_rate": "SL.UEM.TOTL.ZS",
    "fdi_of_gdp": "BX.KLT.DINV.WD.GD.ZS",
}


def _collapse(values):
    """Collapse multiple values to a colon-separated list of values"""
    if isinstance(values, str):
        return values
    if values is None:
        return "all"
    if isinstance(values, list):
        return ";".join([_collapse(v) for v in values])
    return str(values)


def _extract_preferred_field(data, id_or_value):
    """In case the preferred representation of data when the latter has multiple representations"""
    if not id_or_value:
        return data

    if not data:
        return ""

    if isinstance(data, dict):
        if id_or_value in data:
            return data[id_or_value]

    if isinstance(data, list):
        return ",".join([_extract_preferred_field(i, id_or_value) for i in data])

    return data


def _wb_get(paths: dict = None, **kwargs):
    params = copy(kwargs)
    params.setdefault("format", "json")
    params.setdefault("per_page", 20000)

    url = "/".join([WORLD_BANK_URL] + list(itertools.chain.from_iterable([(k, _collapse(paths[k])) for k in paths])))

    response = requests.get(url=url, params=params)
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError:
        raise ValueError(
            "{msg}\nurl={url}\nparams={params}".format(msg=_extract_message(response.text), url=url, params=params)
        )
    if isinstance(data, list) and data and "message" in data[0]:
        try:
            msg = data[0]["message"][0]["value"]
        except (KeyError, IndexError):
            msg = str(msg)

        raise ValueError("{msg}\nurl={url}\nparams={params}".format(msg=msg, url=url, params=params))

    # Redo the request and get the full information when the first response is incomplete
    if isinstance(data, list):
        page_information, data = data
        if "page" not in params:
            current_page = 1
            while current_page < int(page_information["pages"]):
                params["page"] = current_page = int(page_information["page"]) + 1
                response = requests.get(url=url, params=params)
                response.raise_for_status()
                page_information, new_data = response.json()
                data.extend(new_data)

    if not data:
        raise RuntimeError("The request returned no data:\nurl={url}\nparams={params}".format(url=url, params=params))

    return data


def _extract_message(msg):
    """'ï»¿<?xml version="1.0" encoding="utf-8"?>
    <wb:error xmlns:wb="http://www.worldbank.org">
      <wb:message id="175" key="Invalid format">The indicator was not found. It may have been deleted or archived.</wb:message>
    </wb:error>'"""
    if "wb:message" not in msg:
        return msg
    return re.sub(
        re.compile(".*<wb:message[^>]*>", re.DOTALL), "", re.sub(re.compile("</wb:message>.*", re.DOTALL), "", msg)
    )


def _get_meta(name, filters=None, expected=None, **params):
    """Request data and return it in the form of a data frame"""
    filters = _collapse(filters)
    id_or_value = "value"

    if expected and id_or_value not in expected:
        raise ValueError("'id_or_value' should be one of '{}'".format("', '".join(expected)))

    data = _wb_get(paths={name: filters}, **params)

    # We get a list (countries) of dictionary (properties)
    columns = data[0].keys()
    records = {}

    for col in columns:
        records[col] = [_extract_preferred_field(cnt[col], id_or_value) for cnt in data]

    return pd.DataFrame(records, columns=columns)


def get_countries():
    df = _get_meta("country", expected=["id", "iso2code", "value"])

    for col in ["latitude", "longitude"]:
        df[col] = pd.to_numeric(df[col])
    df.rename(
        columns={
            "iso2Code": "code",
            "incomeLevel": "income_level",
            "lendingType": "lending_type",
            "capitalCity": "capital_city",
        },
        inplace=True,
    )
    df["entity_type"] = "country"
    df["exchange"] = "galaxy"
    df["entity_id"] = df[["entity_type", "exchange", "code"]].apply(lambda x: "_".join(x.astype(str)), axis=1)
    df["id"] = df["entity_id"]
    return df


def get_indicators(indicator=None, language=None, id_or_value=None, **params):
    """Return a DataFrame that describes one, multiple or all indicators, indexed by the indicator id.
    :param indicator: None (all indicators), the id of an indicator, or a list of multiple ids
    :param language: Desired language
    :param id_or_value: Choose either 'id' or 'value' for columns 'source' and 'topics'"""

    if id_or_value == "iso2code":
        id_or_value = "id"

    return _get_meta(
        "indicator", indicator, language=language, id_or_value=id_or_value, expected=["id", "value"], **params
    )


def get_indicator_data(indicator, indicator_name=None, country=None, date=None):
    datas = _wb_get(paths={"country": country, "indicator": indicator}, date=date)
    records = [
        {
            "code": item["country"]["id"],
            "timestamp": to_pd_timestamp(item["date"]),
            item["indicator"]["id"] if not indicator_name else indicator_name: item["value"],
        }
        for item in datas
    ]
    df = pd.DataFrame.from_records(data=records)
    df = df.set_index(["code", "timestamp"])
    return df


def get_regions(region=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all regions, indexed by the region id.
    :param region: None (all regions), the id of a region, or a list of multiple ids
    :param language: Desired language"""
    return _get_meta("region", region, language, **params)


def get_sources(source=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all sources, indexed by the source id.
    :param source: None (all sources), the id of a source, or a list of multiple ids
    :param language: Desired language"""
    return _get_meta("source", source, language, **params)


def get_topics(topic=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all sources, indexed by the source id.
    :param topic: None (all topics), the id of a topic, or a list of multiple ids
    :param language: Desired language"""
    return _get_meta("topic", topic, language, **params)


def get_incomelevels(incomelevel=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all income levels, indexed by the IL id.
    :param incomelevel: None (all income levels), the id of an income level, or a list of multiple ids
    :param language: Desired language"""
    return _get_meta("incomelevel", incomelevel, language, **params)


def get_lendingtypes(lendingtype=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all lending types, indexed by the LT id.
    :param lendingtype: None (all lending types), the id of a lending type, or a list of multiple ids
    :param language: Desired language"""
    return _get_meta("lendingtype", lendingtype, language, **params)


def get_economy_data(entity_id, indicators=None, date=None):
    country = get_entity_code(entity_id=entity_id)
    if not indicators:
        indicators = _economy_indicator_map.keys()
    dfs = []
    for indicator in indicators:
        data = get_indicator_data(
            indicator=_economy_indicator_map.get(indicator), indicator_name=indicator, country=country, date=date
        )
        dfs.append(data)
    df = pd.concat(dfs, axis=1)
    df = df.reset_index(drop=False)
    df["entity_id"] = entity_id
    df["id"] = df[["entity_id", "timestamp"]].apply(lambda x: "_".join(x.astype(str)), axis=1)
    df = normal_index_df(df, drop=False)
    return df


if __name__ == "__main__":
    # df = get_countries()
    # print(df)
    df = get_economy_data(entity_id="country_galaxy_CN")
    print(df)
    # df = get_sources()
    # print(df)


# the __all__ is generated
__all__ = [
    "get_countries",
    "get_indicators",
    "get_indicator_data",
    "get_regions",
    "get_sources",
    "get_topics",
    "get_incomelevels",
    "get_lendingtypes",
    "get_economy_data",
]
