# -*- coding: utf-8 -*-
import pandas as pd

from zvt.utils.pd_utils import drop_continue_duplicate


def test_drop_continue_duplicate():
    data1 = [1, 2, 2, 3, 4, 4, 5]
    s = pd.Series(data=data1)
    s1 = drop_continue_duplicate(s=s)
    assert s1.tolist() == [1, 2, 3, 4, 5]

    data2 = [1, 2, 2, 2, 4, 4, 5]

    df = pd.DataFrame(data={"A": data1, "B": data2})
    print(df)
    df1 = drop_continue_duplicate(s=df, col="A")
    assert df1["A"].tolist() == [1, 2, 3, 4, 5]

    df2 = drop_continue_duplicate(s=df, col="B")
    assert df2["A"].tolist() == [1, 2, 4, 5]
