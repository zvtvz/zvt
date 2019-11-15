from zvdata.utils.time_utils import now_pd_timestamp

from zvt.factors.ma.ma_factor import CrossMaFactor
from zvt.factors.target_selector import TargetSelector

my_selector = TargetSelector(start_timestamp='2018-10-01', end_timestamp=now_pd_timestamp())
# add the factors
ma_factor = CrossMaFactor(start_timestamp='2018-10-01', end_timestamp=now_pd_timestamp())

my_selector.add_filter_factor(ma_factor)

my_selector.run()

long_targets = my_selector.get_open_long_targets(timestamp='2019-11-11')
print(long_targets)

print(len(long_targets))
