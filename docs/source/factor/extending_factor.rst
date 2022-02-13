.. _factor.extending_factor:

================
Extending Factor
================

Factor data structure
--------------------------


Write transformer
--------------------------

Computing factor which depends on input data only.
Here is an example: :class:`~.zvt.factors.algorithm.MaTransformer`


Write accumulator
--------------------------

Computing factor which depends on input data and previous result of the factor.
Here is an example: :class:`~.zvt.factors.ma.ma_stats_factor.MaStatsAccumulator.`

