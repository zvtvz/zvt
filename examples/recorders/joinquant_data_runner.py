# -*- coding: utf-8 -*-
import logging
import time
import pandas as pd

from apscheduler.schedulers.background import BackgroundScheduler
from jqdatasdk import auth, get_query_count

from zvt import init_log, zvt_env
from zvt.domain import *
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()

etf_inf_df = {'000001', '000009', '000010', '000015',
 '000016', '000018', '000021', '000028',
 '000029', '000032', '000033', '000036', '000037', '000038', '000042', '000043', '000044',
 '000046', '000048', '000049', '000050', '000051',
 '000056', '000061', '000063', '000064', '000065', '000066', '000067', '000068', '000069',
 '000135', '000140', '000155', '000171', '000300',
 '000802', '000814', '000819', '000821', '000827',
 '000852', '000856', '000858', '000859', '000860', '000861', '000901', '000903', '000905',
 '000906', '000913', '000914', '000922', '000925', '000928', '000932', '000933', '000934', '000938', '000982',
 '000984', '000986', '000987', '000988',
 '000989', '000990', '000991', '000992','000993',
 '399001', '399005', '399006', '399007', '399008', '399291',
 '399293', '399295', '399296', '399324', '399326', '399330','399337', '399348',
 '399362','399364', '399377', '399422', '399437', '399550', '399606', '399610', '399624', '399634', '399660', '399673', '399701', '399702', '399802',
 '399966', '399967', '399971', '399973', '399975', '399976', '399986', '399987', '399989', '399998', '704843',
 '716567', '718465', '718711', '930606',
 '930651', '930652', '930697', '930701', '930703', '930709', '930713', '930726',
 '930738', '930740', '930758', '930782', '930838',
 '930846', '930865', '930916', '930938', '930955', '930997', '930999',
 '931000', '931018', '931023', '931033', '931052', '931066', '931071', '931078',
 '931079', '931087', '931127', '931139', '931140', '931141', '931152', '931159', '931160', '931161', '931163', '931165', '931166', '931167', '931186', '931187',
 '931268', '931373', '931380', '931381', '931406', '931461',
 '950041', '950045', '950047', '950082', '950096',
 '950102', '950105', '950109', '950113', '980001',
 '980017', '990001', 'A08903', 'AU9999', 'C00702', 'CAIMVI', 'CES100','CESMFI',
 'CLLHCT', 'E_ECIA', 'H00816', 'H11014', 'H11017', 'H11077', 'H11098', 'H30021', 'H30035',
 'H30089', 'H30165', 'H30184', 'H30251',
 'H30255', 'H30269', 'H30318', 'H30533', 'H50040', 'H50069', 'HSBBAC', 'IN0017',
 'RA0000', '_GDAXI', '_HSCEI', 'e_SHAU', 'f_IMCI', 'gi_NDX', 'gi_SPX', 'hi_HSI',
 'i_FCHI', 'i_N225'}


@sched.scheduled_job('cron', hour=16, minute=0)
def record_kdata():
    while True:
        email_action = EmailInformer()

        try:
            Stock.record_data(provider='eastmoney', sleeping_time=0.1)
            StockDetail.record_data(provider='eastmoney',sleeping_time=0.1)
            Stock1dKdata.record_data(provider='joinquant', sleeping_time=0.1)  # 前复权
            BalanceSheet.record_data(provider='joinquant', sleeping_time=0.1)
            IncomeStatement.record_data(provider='joinquant',sleeping_time=0.1)
            CashFlowStatement.record_data(provider='joinquant',sleeping_time=0.1)
            StockValuation.record_data(provider='joinquant', sleeping_time=0.1)
            StockTradeDay.record_data(provider='joinquant', sleeping_time=0.1)
            Stock1monBfqKdata.record_data(provider='joinquant' ,sleeping_time=0.1) # 不复权
            Stock1dBfqKdata.record_data(provider='joinquant', sleeping_time=0.1)  # 不复权
            Stock1dHfqKdata.record_data(provider='joinquant', sleeping_time=0.1) # 后复权
            Stock1wkKdata.record_data(provider='joinquant', sleeping_time=0.1)
            Stock1wkHfqKdata.record_data(provider='joinquant', sleeping_time=0.1)
            Stock1wkBfqKdata.record_data(provider='joinquant', sleeping_time=0.1) # 不复权
            Etf.record_data(provider='joinquant', sleeping_time=0.1)
            EtfStock.record_data(provider='joinquant', sleeping_time=0.1)
            Fund.record_data(provider='joinquant', sleeping_time=0.1)
            FundDetail.record_data(provider='joinquant', sleeping_time=0.1)
            FundStock.record_data(provider='joinquant', sleeping_time=0.1)
            FundNetValue.record_data(provider='joinquant', sleeping_time=0.1)
            Etf1dKdata.record_data(provider='joinquant', sleeping_time=0.1)
            Etf1dBfqKdata.record_data(provider='joinquant', sleeping_time=0.1)
            Etf1dHfqKdata.record_data(provider='joinquant', sleeping_time=0.1)

            StockBasicsFactor.record_data(schema='StockBasicsFactor', provider='joinquant', sleeping_time=0.1)
            StockEmotionFactor.record_data(schema='StockEmotionFactor', provider='joinquant', sleeping_time=0.1)
            StockGrowthFactor.record_data(schema='StockGrowthFactor', provider='joinquant', sleeping_time=0.1)
            StockMomentumFactor.record_data(schema='StockMomentumFactor', provider='joinquant', sleeping_time=0.1)
            StockPershareFactor.record_data(schema='StockPershareFactor', provider='joinquant', sleeping_time=0.1)
            StockQualityFactor.record_data(schema='StockQualityFactor', provider='joinquant', sleeping_time=0.1)
            StockRiskFactor.record_data(schema='StockRiskFactor', provider='joinquant', sleeping_time=0.1)
            StockStyleFactor.record_data(schema ='StockStyleFactor', provider='joinquant', sleeping_time=0.1)
            StockTechnicalFactor.record_data(schema ='StockTechnicalFactor', provider='joinquant', sleeping_time=0.1)
            Index1dKdata.record_data(codes=etf_inf_df,provider='joinquant',sleeping_time=0.1)
            Index1monKdata.record_data(provider='joinquant' ,sleeping_time=0.1) # 前复权
            Index1wkKdata.record_data(provider='joinquant',sleeping_time=0.1) # 前复权
            break
        except Exception as e:
            msg = f'joinquant record kdata:{e}'
            logger.exception(msg)

            # email_action.send_message("327714319@qq.com", 'joinquant record kdata error', msg)
            time.sleep(60)

if __name__ == '__main__':
    init_log('joinquant_data_runner.log')
    auth(zvt_env['jq_username'], zvt_env['jq_password'])
    print(f"剩余{get_query_count()['spare'] / 10000}万")
    record_kdata()
    sched.start()
    sched._thread.join()
