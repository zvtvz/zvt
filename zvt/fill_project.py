# script to auto generate some files
from zvt.autocode.generator import gen_kdata_schema, gen_exports
from zvt.contract import AdjustType
from zvt.contract import IntervalLevel


def gen_kdata_schemas():
    # 股票行情
    gen_kdata_schema(pkg='zvt', providers=['joinquant'], entity_type='stock',
                     levels=[level for level in IntervalLevel if level != IntervalLevel.LEVEL_TICK],
                     adjust_types=[None, AdjustType.hfq], entity_in_submodule=True)

    # 板块行情
    gen_kdata_schema(pkg='zvt', providers=['eastmoney'], entity_type='block',
                     levels=[IntervalLevel.LEVEL_1DAY, IntervalLevel.LEVEL_1WEEK, IntervalLevel.LEVEL_1MON],
                     entity_in_submodule=True)

    # etf行情
    gen_kdata_schema(pkg='zvt', providers=['sina'], entity_type='etf',
                     levels=[IntervalLevel.LEVEL_1DAY], entity_in_submodule=True)
    # 指数行情
    gen_kdata_schema(pkg='zvt', providers=['joinquant', 'sina'], entity_type='index',
                     levels=[IntervalLevel.LEVEL_1DAY, IntervalLevel.LEVEL_1WEEK], entity_in_submodule=True)


if __name__ == '__main__':
    # zip_dir(ZVT_TEST_DATA_PATH, zip_file_name=DATA_SAMPLE_ZIP_PATH)
    # gen_exports('api')
    # gen_exports('domain')
    # gen_exports('informer')
    # gen_exports('utils')
    # gen_exports('trader')
    # gen_exports('autocode')
    gen_exports('factors')
    # gen_kdata_schemas()
