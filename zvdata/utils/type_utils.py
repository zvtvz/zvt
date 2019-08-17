# -*- coding: utf-8 -*-
import enum
from typing import List


def create_enum(class_name: str, names: List[str], values: List = None):
    if not values:
        values = names
    return enum.Enum(class_name, dict(zip(names, values)))


def extend_enum(current_enum, names: List[str], values: List = None):
    if not values:
        values = names

    for item in current_enum:
        names.append(item.name)
        values.append(item.value)

    return enum.Enum(current_enum.__name__, dict(zip(names, values)))
