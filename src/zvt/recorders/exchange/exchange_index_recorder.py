# -*- coding: utf-8 -*-

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain import Index
from zvt.recorders.exchange.api import cn_index_api, cs_index_api


class ExchangeIndexRecorder(Recorder):
    provider = "exchange"
    data_schema = Index

    def run(self):
        # 深圳
        self.record_cn_index("sz")
        # 国证
        self.record_cn_index("cni")

        # 上海
        self.record_cs_index("sh")
        # 中证
        self.record_cs_index("csi")

    # 中证，上海
    def record_cs_index(self, index_type):
        df = cs_index_api.get_cs_index(index_type=index_type)
        df_to_db(data_schema=self.data_schema, df=df, provider=self.provider, force_update=True)
        self.logger.info(f"finish record {index_type} index")

    # 国证，深圳
    def record_cn_index(self, index_type):
        if index_type == "cni":
            category_map_url = cn_index_api.cni_category_map_url
        elif index_type == "sz":
            category_map_url = cn_index_api.sz_category_map_url
        else:
            self.logger.error(f"not support index_type: {index_type}")
            assert False

        for category, _ in category_map_url.items():
            df = cn_index_api.get_cn_index(index_type=index_type, category=category)
            df_to_db(data_schema=self.data_schema, df=df, provider=self.provider, force_update=True)
            self.logger.info(f"finish record {index_type} index:{category.value}")


if __name__ == "__main__":
    # init_log('china_stock_category.log')
    ExchangeIndexRecorder().run()

# the __all__ is generated
__all__ = ["ExchangeIndexRecorder"]
