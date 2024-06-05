# -*- coding: utf-8 -*-
def update_model(db_model, schema):
    for key, value in schema.dict().items():
        if value is not None:
            setattr(db_model, key, value)


# the __all__ is generated
__all__ = ["update_model"]
