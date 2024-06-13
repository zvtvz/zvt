# -*- coding: utf-8 -*-
import json
from typing import Type, List

from zvt.contract.api import del_data, get_db_session
from zvt.contract.zvt_info import StateMixin
from zvt.utils.str_utils import to_snake_str


class StatefulService(object):
    """
    Base service with state could be stored in state_schema
    """

    #: state schema
    state_schema: Type[StateMixin] = None

    #: name of the service, default name of class if not set manually
    name = None

    def __init__(self) -> None:
        assert self.state_schema is not None
        if self.name is None:
            self.name = to_snake_str(type(self).__name__)
        self.state_session = get_db_session(data_schema=self.state_schema, provider="zvt")

    def clear_state_data(self, entity_id=None):
        """
        clear state of the entity

        :param entity_id: entity id
        """
        filters = [self.state_schema.state_name == self.name]
        if entity_id:
            filters = filters + [self.state_schema.entity_id == entity_id]
        del_data(self.state_schema, filters=filters)

    def decode_state(self, state: str):
        """
        decode state

        :param state:
        :return:
        """

        return json.loads(state, object_hook=self.state_object_hook())

    def encode_state(self, state: object):
        """
        encode state

        :param state:
        :return:
        """

        return json.dumps(state, cls=self.state_encoder())

    def state_object_hook(self):
        return None

    def state_encoder(self):
        return None


class OneStateService(StatefulService):
    """
    StatefulService which saving all states in one object
    """

    def __init__(self) -> None:
        super().__init__()
        self.state_domain = self.state_schema.get_by_id(id=self.name)
        if self.state_domain:
            self.state: dict = self.decode_state(self.state_domain.state)
        else:
            self.state = None

    def persist_state(self):
        state_str = self.encode_state(self.state)
        if not self.state_domain:
            self.state_domain = self.state_schema(id=self.name, entity_id=self.name, state_name=self.name)
        self.state_domain.state = state_str
        self.state_session.add(self.state_domain)
        self.state_session.commit()


class EntityStateService(StatefulService):
    """
    StatefulService which saving one state one entity
    """

    def __init__(self, entity_ids) -> None:
        super().__init__()
        self.entity_ids = entity_ids
        state_domains: List[StateMixin] = self.state_schema.query_data(
            filters=[self.state_schema.state_name == self.name], entity_ids=self.entity_ids, return_type="domain"
        )

        #: entity_id:state
        self.states: dict = {}
        if state_domains:
            for state in state_domains:
                self.states[state.entity_id] = self.decode_state(state.state)

    def persist_state(self, entity_id):
        state = self.states.get(entity_id)
        if state:
            domain_id = f"{self.name}_{entity_id}"
            state_domain = self.state_schema.get_by_id(domain_id)
            state_str = self.encode_state(state)
            if not state_domain:
                state_domain = self.state_schema(id=domain_id, entity_id=entity_id, state_name=self.name)
            state_domain.state = state_str
            self.state_session.add(state_domain)
            self.state_session.commit()


# the __all__ is generated
__all__ = ["StatefulService", "OneStateService", "EntityStateService"]
