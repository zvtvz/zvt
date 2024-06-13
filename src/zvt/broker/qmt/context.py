# -*- coding: utf-8 -*-
from typing import Optional

from zvt import zvt_env
from zvt.broker.qmt.qmt_account import QmtStockAccount


class QmtContext(object):
    def __init__(self):
        self.qmt_account: Optional[QmtStockAccount] = None


qmt_context = QmtContext()


def init_qmt_account(qmt_mini_data_path=None, qmt_account_id=None):
    if not qmt_mini_data_path:
        qmt_mini_data_path = zvt_env["qmt_mini_data_path"]
    if not qmt_account_id:
        qmt_account_id = zvt_env["qmt_account_id"]
    qmt_context.qmt_account = QmtStockAccount(
        path=qmt_mini_data_path, account_id=qmt_account_id, trader_name="zvt", session_id=None
    )


init_qmt_account()


# the __all__ is generated
__all__ = ["QmtContext", "init_qmt_account"]
