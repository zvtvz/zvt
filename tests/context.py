# -*- coding: utf-8 -*-

def init_context():
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from zvt import settings
    settings.DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasample'))
