# -*- coding: utf-8 -*-
import os
import sys

os.environ.setdefault("TESTING_ZVT", "True")
os.environ.setdefault("SQLALCHEMY_WARN_20", "1")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
