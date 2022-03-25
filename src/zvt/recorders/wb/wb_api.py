# -*- coding: utf-8 -*-
import re
from copy import copy

import numpy as np
import pandas as pd
from requests import get, HTTPError

language = "en"
id_or_value = "value"

WORLD_BANK_URL = "http://api.worldbank.org/v2"


# thanks to https://github.com/mwouts/world_bank_data


class WBRequestError(HTTPError):
    """An error occured when downloading the WB data"""


def collapse(values):
    """Collapse multiple values to a colon-separated list of values"""
    if isinstance(values, str):
        return values
    if values is None:
        return "all"
    if isinstance(values, list):
        return ";".join([collapse(v) for v in values])
    return str(values)


def extract_preferred_field(data, id_or_value):
    """In case the preferred representation of data when the latter has multiple representations"""
    if not id_or_value:
        return data

    if not data:
        return ""

    if isinstance(data, dict):
        if id_or_value in data:
            return data[id_or_value]

    if isinstance(data, list):
        return ",".join([extract_preferred_field(i, id_or_value) for i in data])

    return data


def wb_get(*args, **kwargs):
    """Request the World Bank for the desired information"""
    params = copy(kwargs)
    language = params.pop("language", "en")
    params.setdefault("format", "json")
    params.setdefault("per_page", 20000)

    # collapse the list of countries to a single str
    if len(args) > 1:
        args = list(args)
        args[1] = collapse(args[1])

    if "topic" in params:
        args = ["topic", str(params.pop("topic"))] + args

    if language != "en":
        args = [language] + args

    url = "/".join([WORLD_BANK_URL] + args)

    response = get(url=url, params=params)
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError:  # simplejson.errors.JSONDecodeError derives from ValueError
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
    if params["format"] == "json" and isinstance(data, list):
        page_information, data = data
        if "page" not in params:
            current_page = 1
            while current_page < int(page_information["pages"]):
                params["page"] = current_page = int(page_information["page"]) + 1
                response = get(url=url, params=params)
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


def wb_get_table(name, only=None, language="en", id_or_value=None, expected=None, **params):
    """Request data and return it in the form of a data frame"""
    only = collapse(only)
    id_or_value = id_or_value or "value"

    if expected and id_or_value not in expected:
        raise ValueError("'id_or_value' should be one of '{}'".format("', '".join(expected)))

    if language:
        params["language"] = language
    data = wb_get(name, only, **params)

    # We get a list (countries) of dictionary (properties)
    columns = data[0].keys()
    table = {}

    for col in columns:
        table[col] = [extract_preferred_field(cnt[col], id_or_value) for cnt in data]

    table = pd.DataFrame(table, columns=columns)

    if table["id"].any():
        return table.set_index("id")

    table.pop("id")
    return table.set_index("code")


def get_countries():
    df = wb_get_table("country", language=language, id_or_value=id_or_value, expected=["id", "iso2code", "value"])

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
    df["entity_id"] = df["id"]

    return df


def get_indicators(indicator=None, language=None, id_or_value=None, **params):
    """Return a DataFrame that describes one, multiple or all indicators, indexed by the indicator id.
    :param indicator: None (all indicators), the id of an indicator, or a list of multiple ids
    :param language: Desired language
    :param id_or_value: Choose either 'id' or 'value' for columns 'source' and 'topics'"""

    if id_or_value == "iso2code":
        id_or_value = "id"

    return wb_get_table(
        "indicator", indicator, language=language, id_or_value=id_or_value, expected=["id", "value"], **params
    )


def get_series(indicator, country=None, id_or_value=None, simplify_index=False, **params):
    """Return a Series with the indicator data.
    :param indicator: Indicator code (see indicators())
    :param country: None (all countries), the id of a country, or a list of multiple country codes
    :param id_or_value: Should the index have codes or labels?
    :param simplify_index: Drop index levels that have a single value
    :param params: Additional parameters for the World Bank API, like date or mrv"""

    id_or_value = id_or_value or "value"
    params["format"] = "jsonstat"

    idx = wb_get("country", country, "indicator", indicator, **params)
    _, idx = idx.popitem()

    dimension = idx.pop("dimension")
    value = idx.pop("value")

    index = [_parse_category(dimension[dim], id_or_value == "value") for dim in dimension["id"]]
    if not id_or_value:
        for idx, name in zip(index, dimension["id"]):
            idx.name = name

    if simplify_index:
        index = [dim for dim in index if len(dim) != 1]

    if len(index) > 1:
        # Our series is indexed by a multi-index
        index = pd.MultiIndex.from_product(index, names=[dim.name for dim in index])
    elif len(index) == 1:
        # A simple index is enough
        index = index[0]
    else:
        # Index has dimension zero. Data should be a scalar
        assert len(value) == 1, "Data has no dimension and was expected to be a scalar"
        return value[0]

    return pd.Series(value, index=index, name=indicator)


def _parse_category(cat, use_labels):
    name = cat["label"]
    cat = cat["category"]

    index = np.array(list(cat["index"].values()))
    codes = np.array(list(cat["index"].keys()))

    codes = pd.Series(codes, index=index, name=name).sort_index()
    if not use_labels:
        return codes

    codes2 = np.array(list(cat["label"].keys()))
    labels = np.array(list(cat["label"].values()))
    labels = pd.Series(labels, index=codes2, name=name).sort_index()

    return pd.Series(labels.loc[codes].values, index=codes.index, name=name)


def get_regions(region=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all regions, indexed by the region id.
    :param region: None (all regions), the id of a region, or a list of multiple ids
    :param language: Desired language"""
    return wb_get_table("region", region, language, **params)


def get_sources(source=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all sources, indexed by the source id.
    :param source: None (all sources), the id of a source, or a list of multiple ids
    :param language: Desired language"""
    return wb_get_table("source", source, language, **params)


def get_topics(topic=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all sources, indexed by the source id.
    :param topic: None (all topics), the id of a topic, or a list of multiple ids
    :param language: Desired language"""
    return wb_get_table("topic", topic, language, **params)


def get_incomelevels(incomelevel=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all income levels, indexed by the IL id.
    :param incomelevel: None (all income levels), the id of an income level, or a list of multiple ids
    :param language: Desired language"""
    return wb_get_table("incomelevel", incomelevel, language, **params)


def get_lendingtypes(lendingtype=None, language=None, **params):
    """Return a DataFrame that describes one, multiple or all lending types, indexed by the LT id.
    :param lendingtype: None (all lending types), the id of a lending type, or a list of multiple ids
    :param language: Desired language"""
    return wb_get_table("lendingtype", lendingtype, language, **params)


if __name__ == "__main__":
    df = get_countries()
    print(df)
# the __all__ is generated
__all__ = [
    "WBRequestError",
    "collapse",
    "extract_preferred_field",
    "wb_get",
    "wb_get_table",
    "get_countries",
    "get_indicators",
    "get_series",
    "get_regions",
    "get_sources",
    "get_topics",
    "get_incomelevels",
    "get_lendingtypes",
]
