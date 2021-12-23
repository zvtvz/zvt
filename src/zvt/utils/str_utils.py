# -*- coding: utf-8 -*-


def to_snake_str(input: str) -> str:
    parts = []
    part = ""
    for c in input:
        if c.isupper() or c.isdigit():
            if part:
                parts.append(part)
            part = c.lower()
        else:
            part = part + c

    parts.append(part)

    if len(parts) > 1:
        return "_".join(parts)
    elif parts:
        return parts[0]


def to_camel_str(input: str) -> str:
    parts = input.split("_")
    domain_name = ""
    for part in parts:
        domain_name = domain_name + part.capitalize()
    return domain_name


# the __all__ is generated
__all__ = ["to_snake_str", "to_camel_str"]
