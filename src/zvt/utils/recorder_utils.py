# -*- coding: utf-8 -*-
import logging
import time
from typing import Type

import zvt as zvt
from zvt import zvt_config
from zvt.informer import EmailInformer

logger = logging.getLogger("__name__")


def run_data_recorder(
    domain: Type["zvt.contract.Mixin"],
    entity_provider=None,
    data_provider=None,
    entity_ids=None,
    split_entity_ids_size=0,
    retry_times=10,
    sleeping_time=10,
    return_unfinished=False,
    **recorder_kv,
):
    if (entity_ids is not None) and split_entity_ids_size > 0:
        import numpy as np

        size = len(entity_ids)
        if size >= split_entity_ids_size:
            step_size = int(size / split_entity_ids_size)
            if size % split_entity_ids_size:
                step_size = step_size + 1
        else:
            step_size = 1

        entity_ids_list = np.array_split(entity_ids, step_size)

        for split_entity_ids in entity_ids_list:
            run_data_recorder(
                domain=domain,
                entity_provider=entity_provider,
                data_provider=data_provider,
                entity_ids=list(split_entity_ids),
                split_entity_ids_size=0,
                retry_times=retry_times,
                sleeping_time=sleeping_time,
                return_unfinished=return_unfinished,
                **recorder_kv,
            )
            time.sleep(90)
        return

    logger.info(f" record data: {domain.__name__}, entity_provider: {entity_provider}, data_provider: {data_provider}")

    unfinished_entity_ids = entity_ids
    email_action = EmailInformer()

    while retry_times > 0:
        try:
            entity_size = len(entity_ids) if entity_ids else "all"

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

            msg = f"record {domain.__name__} {entity_size} success"
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
