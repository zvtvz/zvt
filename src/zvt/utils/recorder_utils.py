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
    return_unfinished=False,
    **recorder_kv,
):
    logger.info(f" record data: {domain.__name__}, entity_provider: {entity_provider}, data_provider: {data_provider}")

    unfinished_entity_ids = entity_ids
    email_action = EmailInformer()

    while retry_times > 0:
        try:
            if return_unfinished:
                unfinished_entity_ids = domain.record_data(
                    entity_ids=unfinished_entity_ids,
                    provider=data_provider,
                    sleeping_time=sleeping_time,
                    return_unfinished=return_unfinished,
                    **recorder_kv,
                )
                if unfinished_entity_ids:
                    logger.info(f"unfinished_entity_ids({len(unfinished_entity_ids)}): {unfinished_entity_ids}")
                    raise Exception("Would retry with unfinished latter!")
            else:
                domain.record_data(
                    entity_ids=entity_ids,
                    provider=data_provider,
                    sleeping_time=sleeping_time,
                    return_unfinished=return_unfinished,
                    **recorder_kv,
                )

            msg = f"record {domain.__name__} success"
            logger.info(msg)
            email_action.send_message(zvt_config["email_username"], msg, msg)
            break
        except Exception as e:
            logger.exception("report error:{}".format(e))
            time.sleep(60 * 2)
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
