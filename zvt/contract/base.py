# -*- coding: utf-8 -*-
import json
from typing import Type

from zvt.contract.api import del_data, get_db_session
from zvt.contract.schema import Mixin


class StatefulService(object):
    state_schema: Type[Mixin] = None
    name = None

    def __init__(self) -> None:
        assert self.state_schema is not None
        self.state_session = get_db_session(data_schema=self.state_schema, provider='zvt')
        self.state_domain = self.state_schema.get_one(id=self.get_state_entity_id())
        if self.state_domain:
            self.state: dict = self.decode_state(self.state_domain.state)

    def get_state_entity_id(self):
        if self.name is not None:
            return self.name
        return type(self).__name__.lower()

    def clear_state_data(self):
        del_data(self.state_schema, filters=[self.state_schema.entity_id == self.get_state_entity_id()])

    def decode_state(self, state: str):
        # 反序列化
        return json.loads(state, object_hook=self.state_object_hook())

    def encode_state(self, state: object):
        # 序列化
        return json.dumps(state, cls=self.state_encoder())

    def state_object_hook(self):
        return None

    def state_encoder(self):
        return None

    def persist_state(self):
        state_str = self.encode_state(self.state)
        if not self.state_domain:
            self.state_domain = self.state_schema(id=self.get_state_entity_id(), entity_id=self.get_state_entity_id(),
                                                  recoder_name=self.name, state=state_str)
        self.state_session.add(self.state_domain)
        self.state_session.commit()
