# -*- coding: utf-8 -*-
import eastmoneypy
import requests

from zvt import zvt_config
from zvt.contract.api import get_entities
from zvt.informer import EmailInformer


def inform_email(entity_ids, entity_type, target_date, title, provider):
    msg = "no targets"
    if entity_ids:
        entities = get_entities(provider=provider, entity_type=entity_type, entity_ids=entity_ids, return_type="domain")
        assert len(entities) == len(entity_ids)

        infos = [f"{entity.name}({entity.code})" for entity in entities]
        msg = "\n".join(infos) + "\n"

        EmailInformer().send_message(zvt_config["email_username"], f"{target_date} {title}", msg)


def add_to_eastmoney(codes, group, entity_type="stock", over_write=True):
    with requests.Session() as session:
        group_id = eastmoneypy.get_group_id(group, session=session)

        need_create_group = False

        if not group_id:
            need_create_group = True

        if group_id and over_write:
            eastmoneypy.del_group(group_name=group, session=session)
            need_create_group = True

        if need_create_group:
            result = eastmoneypy.create_group(group_name=group, session=session)
            group_id = result["gid"]

        codes = list(set(codes))
        for code in codes:
            eastmoneypy.add_to_group(code=code, entity_type=entity_type, group_id=group_id, session=session)


def clean_groups(keep):
    if keep is None:
        keep = ["自选股", "练气", "重要板块", "主线"]

    with requests.Session() as session:
        groups = eastmoneypy.get_groups(session=session)
        groups_to_clean = [group["gid"] for group in groups if group["gname"] not in keep]
        for gid in groups_to_clean:
            eastmoneypy.del_group(group_id=gid, session=session)


# the __all__ is generated
__all__ = ["inform_email", "add_to_eastmoney", "clean_groups"]
