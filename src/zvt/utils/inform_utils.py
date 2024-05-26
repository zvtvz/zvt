# -*- coding: utf-8 -*-
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
