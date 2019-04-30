# -*- coding: utf-8 -*-
from zvt.domain import Provider
from zvt.recorders.common.china_stock_list_spider import ChinaStockListSpider


def run():
    ChinaStockListSpider(provider=Provider.SINA).run()


if __name__ == '__main__':
    run()
