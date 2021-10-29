# -*- coding: utf-8 -*-
import logging
import time
from typing import Type

from examples.utils import add_to_eastmoney
from zvt import zvt_config
from zvt.api import get_top_volume_entities
from zvt.api.kdata import get_latest_kdata_date
from zvt.contract import AdjustType
from zvt.contract.api import get_entities, get_entity_schema
from zvt.contract.factor import Factor
from zvt.factors import TargetSelector, SelectMode
from zvt.informer import EmailInformer
from zvt.utils import next_date

logger = logging.getLogger('__name__')


def report_targets(factor_cls: Type[Factor],
                   entity_provider,
                   data_provider,
                   title,
                   entity_type='stock',
                   em_group=None,
                   em_group_over_write=True,
                   filter_by_volume=True,
                   adjust_type=None,
                   start_timestamp='2019-01-01',
                   **factor_kv):
    logger.info(
        f'entity_provider: {entity_provider}, data_provider: {data_provider}, entity_type: {entity_type}, start_timestamp: {start_timestamp}')
    error_count = 0

    while error_count <= 10:
        email_action = EmailInformer()

        try:
            if entity_type == 'stock' and not adjust_type:
                adjust_type = AdjustType.hfq

            target_date = get_latest_kdata_date(entity_type=entity_type, adjust_type=adjust_type)
            logger.info(f'target_date :{target_date}')

            current_entity_pool = None
            if filter_by_volume:
                # 成交量
                vol_df = get_top_volume_entities(entity_type=entity_type,
                                                 start_timestamp=next_date(target_date, -30),
                                                 end_timestamp=target_date,
                                                 pct=0.4)
                current_entity_pool = vol_df.index.tolist()
                logger.info(f'current_entity_pool({len(current_entity_pool)}): {current_entity_pool}')

            # add the factor
            my_selector = TargetSelector(start_timestamp=start_timestamp, end_timestamp=target_date,
                                         select_mode=SelectMode.condition_or)
            entity_schema = get_entity_schema(entity_type=entity_type)
            tech_factor = factor_cls(entity_schema=entity_schema, entity_provider=entity_provider,
                                     provider=data_provider, entity_ids=current_entity_pool,
                                     start_timestamp=start_timestamp, end_timestamp=target_date, **factor_kv)
            my_selector.add_factor(tech_factor)

            my_selector.run()

            long_stocks = my_selector.get_open_long_targets(timestamp=target_date)

            msg = 'no targets'

            if long_stocks:
                entities = get_entities(provider=entity_provider, entity_type=entity_type, entity_ids=long_stocks,
                                        return_type='domain')
                if em_group:
                    try:
                        codes = [entity.code for entity in entities]
                        add_to_eastmoney(codes=codes, entity_type=entity_type, group=em_group,
                                         over_write=em_group_over_write)
                    except Exception as e:
                        email_action.send_message(zvt_config['email_username'],
                                                  f'report {entity_type}{factor_cls.__name__} error',
                                                  f'report {entity_type}{factor_cls.__name__} error: {e}')

                infos = [f'{entity.name}({entity.code})' for entity in entities]
                msg = '\n'.join(infos) + '\n'

            logger.info(msg)

            email_action.send_message(zvt_config['email_username'], f'{target_date} {title}', msg)

            break
        except Exception as e:
            logger.exception('report error:{}'.format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message(zvt_config['email_username'],
                                          f'report {entity_type}{factor_cls.__name__} error',
                                          f'report {entity_type}{factor_cls.__name__} error: {e}')


if __name__ == '__main__':
    from zvt.factors import VolumeUpMaFactor

    report_targets(factor_cls=VolumeUpMaFactor, entity_provider='joinquant', data_provider='joinquant', em_group='年线股票',
                   title='放量突破(半)年线股票', entity_type='stock', em_group_over_write=True, filter_by_volume=True,
                   adjust_type=AdjustType.hfq, start_timestamp='2019-01-01',
                   # factor args
                   windows=[120, 250], over_mode='or', up_intervals=50, turnover_threshold=400000000)
# the __all__ is generated
__all__ = ['report_targets']
