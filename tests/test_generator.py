# -*- coding: utf-8 -*-
from zvt.autocode.generator import _remove_start_end


def test_remove_start_end():
    cls = _remove_start_end("class A(object)", "class ", "(")
    assert cls == "A"

    func = _remove_start_end("def aaa(arg1, arg2)", "def ", "(")
    assert func == "aaa"

    var = _remove_start_end("zvt_env = ", "", " =")
    assert var == "zvt_env"
