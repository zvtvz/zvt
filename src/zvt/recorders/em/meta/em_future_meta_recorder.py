# -*- coding: utf-8 -*-

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain import Future
from zvt.recorders.em import em_api


class EMFutureRecorder(Recorder):
    provider = "em"
    data_schema = Future

    def run(self):
        df = em_api.get_tradable_list(entity_type="future")
        self.logger.info(df)
        df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)


if __name__ == "__main__":
    recorder = EMFutureRecorder(force_update=True)
    recorder.run()


# the __all__ is generated
__all__ = ["EMFutureRecorder"]
