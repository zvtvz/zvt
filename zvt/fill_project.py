# script to auto generate some files
from zvt.autocode.generator import gen_kdata_schema, gen_exports
from zvt.contract import AdjustType
from zvt.contract import IntervalLevel


def gen_kdata_schemas():
    # A股行情
    gen_kdata_schema(
        pkg="zvt",
        providers=["joinquant", "em"],
        entity_type="stock",
        levels=[level for level in IntervalLevel if level != IntervalLevel.LEVEL_TICK],
        adjust_types=[None, AdjustType.hfq],
        entity_in_submodule=True,
    )

    # 美股
    gen_kdata_schema(
        pkg="zvt",
        providers=["em"],
        entity_type="stockus",
        levels=[IntervalLevel.LEVEL_1DAY],
        adjust_types=[None, AdjustType.hfq],
        entity_in_submodule=True,
    )

    # 港股
    gen_kdata_schema(
        pkg="zvt",
        providers=["em"],
        entity_type="stockhk",
        levels=[IntervalLevel.LEVEL_1DAY],
        adjust_types=[None, AdjustType.hfq],
        entity_in_submodule=True,
    )

    # 板块行情
    gen_kdata_schema(
        pkg="zvt",
        providers=["em"],
        entity_type="block",
        levels=[IntervalLevel.LEVEL_1DAY, IntervalLevel.LEVEL_1WEEK, IntervalLevel.LEVEL_1MON],
        entity_in_submodule=True,
    )

    # 指数行情
    gen_kdata_schema(
        pkg="zvt",
        providers=["em", "sina"],
        entity_type="index",
        levels=[IntervalLevel.LEVEL_1DAY, IntervalLevel.LEVEL_1WEEK],
        entity_in_submodule=True,
    )

    # etf行情
    gen_kdata_schema(
        pkg="zvt", providers=["sina"], entity_type="etf", levels=[IntervalLevel.LEVEL_1DAY], entity_in_submodule=True
    )


if __name__ == "__main__":
    # zip_dir(ZVT_TEST_DATA_PATH, zip_file_name=DATA_SAMPLE_ZIP_PATH)
    # gen_exports('contract',export_modules=['schema'])
    gen_exports("informer")
    # gen_exports('recorders')
    # gen_exports('domain')
    # gen_exports('informer')
    # gen_exports('api')
    # gen_exports('trader')
    # gen_exports('autocode')
    # gen_exports('ml')
    # gen_kdata_schemas()
