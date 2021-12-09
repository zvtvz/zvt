# -*- coding: utf-8 -*-
import logging
import time
from typing import Type

from zvt import zvt_config
from zvt.contract import Mixin
from zvt.informer import EmailInformer

logger = logging.getLogger("__name__")


def run_data_recorder(
    domain: Type[Mixin],
    entity_provider=None,
    data_provider=None,
    entity_ids=None,
    retry_times=10,
    sleeping_time=10,
    **recorder_kv,
):
    logger.info(f" record data: {domain.__name__}, entity_provider: {entity_provider}, data_provider: {data_provider}")

    while retry_times > 0:
        email_action = EmailInformer()

        try:
            domain.record_data(
                entity_ids=entity_ids, provider=data_provider, sleeping_time=sleeping_time, **recorder_kv
            )
            msg = f"record {domain.__name__} success"
            logger.info(msg)
            email_action.send_message(zvt_config["email_username"], msg, msg)
            break
        except Exception as e:
            logger.exception("report error:{}".format(e))
            time.sleep(60 * 3)
            retry_times = retry_times - 1
            if retry_times == 0:
                email_action.send_message(
                    zvt_config["email_username"],
                    f"record {domain.__name__} error",
                    f"record {domain.__name__} error: {e}",
                )


if __name__ == "__main__":
    run_data_recorder()
# the __all__ is generated
__all__ = ["run_data_recorder"]
