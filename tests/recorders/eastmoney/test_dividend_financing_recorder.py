# -*- coding: utf-8 -*-
from ...context import init_test_context

init_test_context()

from zvt.settings import SAMPLE_STOCK_CODES

from zvt.recorders.eastmoney.dividend_financing.dividend_detail_recorder import DividendDetailRecorder
from zvt.recorders.eastmoney.dividend_financing.dividend_financing_recorder import DividendFinancingRecorder
from zvt.recorders.eastmoney.dividend_financing.rights_issue_detail_recorder import RightsIssueDetailRecorder
from zvt.recorders.eastmoney.dividend_financing.spo_detail_recorder import SPODetailRecorder


def test_dividend_detail():
    recorder = DividendDetailRecorder(codes=SAMPLE_STOCK_CODES)
    try:
        recorder.run()
    except:
        assert False


def test_rights_issue_detail():
    recorder = RightsIssueDetailRecorder(codes=SAMPLE_STOCK_CODES)
    try:
        recorder.run()
    except:
        assert False


def test_spo_detail():
    recorder = SPODetailRecorder(codes=SAMPLE_STOCK_CODES)
    try:
        recorder.run()
    except:
        assert False


def test_dividend_financing():
    recorder = DividendFinancingRecorder(codes=SAMPLE_STOCK_CODES)
    try:
        recorder.run()
    except:
        assert False
