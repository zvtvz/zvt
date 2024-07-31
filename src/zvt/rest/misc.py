# -*- coding: utf-8 -*-
from fastapi import APIRouter

from zvt.misc import misc_service
from zvt.misc.misc_models import TimeMessage

misc_router = APIRouter(
    prefix="/api/misc",
    tags=["misc"],
    responses={404: {"description": "Not found"}},
)


@misc_router.get(
    "/time_message",
    response_model=TimeMessage,
)
def get_time_message():
    """
    Get time message
    """
    return misc_service.get_time_message()
