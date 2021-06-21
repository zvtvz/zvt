# -*- coding: utf-8 -*-
import json

from zvt.contract.api import del_data


class Bean(object):

    def __init__(self) -> None:
        super().__init__()
        self.__dict__

    def dict(self):
        return self.__dict__

    def from_dct(self, dct: dict):
        if dct:
            for k in dct:
                self.__dict__[k] = dct[k]


class StatefulService(object):
    state_schema = None
    state_session = None

    state = None

    def __init__(self) -> None:
        super().__init__()

    def get_stateful_id(self):
        return type(self).__name__.lower()

    def init_state(self):
        states = self.state_schema.query_data(filters=[self.state_schema.entity_id == self.get_stateful_id()],
                                              return_type='domain')
        if states:
            self.recorder_state = states[0]
            self.state: dict = self.decode_state(self.recorder_state.state)

    def clear_state_data(self):
        del_data(self.state_schema, filters=[self.state_schema.entity_id == self.get_stateful_id])

    def decode_state(self, state: str):
        return json.loads(state, object_hook=self.state_object_hook())

    def encode_state(self, state: object):
        return json.dumps(state, cls=self.state_encoder())

    def state_object_hook(self):
        return None

    def state_encoder(self):
        return None

    def persist_state(self, entity_id, state):
        state_str = self.encode_state(state)
        if self.state_domain:
            self.state_domain.state = state_str
        else:
            domain_id = f'{self.name}_{entity_id}'
            self.state_domain = self.state_schema(id=domain_id, entity_id=entity_id,
                                                  recoder_name=self.name,
                                                  state=state_str)
        self.state_session.add(self.recorder_state)
        self.state_session.commit()
