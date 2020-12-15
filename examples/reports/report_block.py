# -*- coding: utf-8 -*-
import logging
import time
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log
from zvt.contract import IntervalLevel
from zvt.domain import Block, BlockMoneyFlow, BlockCategory
from zvt.factors import TargetSelector
from zvt.factors.technical import BlockMoneyFlowFactor
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


class IndustryBlockSelector(TargetSelector):

    def __init__(self, entity_ids=None, entity_schema=Block, exchanges=None, codes=None, the_timestamp=None,
                 start_timestamp=None, end_timestamp=None, long_threshold=0.8, short_threshold=0.2,
                 level=IntervalLevel.LEVEL_1DAY, provider='sina') -> None:
        super().__init__(entity_ids, entity_schema, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         long_threshold, short_threshold, level, provider)

    def init_factors(self, entity_ids, entity_schema, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                     level):
        block_factor = BlockMoneyFlowFactor(start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                            provider='sina', window=5)
        self.score_factors.append(block_factor)


class ConceptBlockSelector(TargetSelector):

    def __init__(self, entity_ids=None, entity_schema=Block, exchanges=None, codes=None, the_timestamp=None,
                 start_timestamp=None, end_timestamp=None, long_threshold=0.8, short_threshold=0.2,
                 level=IntervalLevel.LEVEL_1DAY, provider='sina') -> None:
        super().__init__(entity_ids, entity_schema, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                         long_threshold, short_threshold, level, provider)

    def init_factors(self, entity_ids, entity_schema, exchanges, codes, the_timestamp, start_timestamp, end_timestamp,
                     level):
        block_factor = BlockMoneyFlowFactor(start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                            provider='sina', window=10, category=BlockCategory.concept.value)
        self.score_factors.append(block_factor)


@sched.scheduled_job('cron', hour=15, minute=50, day_of_week='mon-fri')
def report_block():
    while True:
        error_count = 0
        email_action = EmailInformer(ssl=True)

        try:
            latest_day: BlockMoneyFlow = BlockMoneyFlow.query_data(order=BlockMoneyFlow.timestamp.desc(), limit=1,
                                                                   return_type='domain')
            target_date = latest_day[0].timestamp

            msg = ''
            # 行业板块
            industry_block_selector = IndustryBlockSelector(start_timestamp='2020-01-01', long_threshold=0.8)
            industry_block_selector.run()
            industry_long_blocks = industry_block_selector.get_open_long_targets(timestamp=target_date)

            if industry_long_blocks:
                blocks: List[Block] = Block.query_data(provider='sina', entity_ids=industry_long_blocks,
                                                       return_type='domain')

                info = [f'{block.name}({block.code})' for block in blocks]
                msg = msg + '行业板块:' + ' '.join(info) + '\n'

            # 概念板块
            concept_block_selector = ConceptBlockSelector(start_timestamp='2020-01-01', long_threshold=0.85)
            concept_block_selector.run()
            concept_long_blocks = concept_block_selector.get_open_long_targets(timestamp=target_date)

            if concept_long_blocks:
                blocks: List[Block] = Block.query_data(provider='sina', entity_ids=concept_long_blocks,
                                                       return_type='domain')

                info = [f'{block.name}({block.code})' for block in blocks]
                msg = msg + '概念板块' + ' '.join(info) + '\n'

            logger.info(msg)
            email_action.send_message('5533061@qq.com', f'{target_date} 资金流入板块评分结果', msg)
            break
        except Exception as e:
            logger.exception('report_block error:{}'.format(e))
            time.sleep(60 * 3)
            error_count = error_count + 1
            if error_count == 10:
                email_action.send_message("5533061@qq.com", f'report_block error',
                                          'report_block error:{}'.format(e))


if __name__ == '__main__':
    init_log('report_block.log')

    report_block()

    sched.start()

    sched._thread.join()
