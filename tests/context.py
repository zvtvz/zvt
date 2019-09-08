# -*- coding: utf-8 -*-

def init_test_context():
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
