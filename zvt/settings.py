# -*- coding: utf-8 -*-
import os

# please change the path to your real store path
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','datasample'))
UI_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','ui'))

if not DATA_PATH:
    DATA_PATH = os.environ.get('ZVT_DATA_PATH')

JQ_ACCOUNT = ''
if not JQ_ACCOUNT:
    JQ_ACCOUNT = os.environ.get('JQ_ACCOUNT')

JQ_PASSWD = ''
if not JQ_PASSWD:
    JQ_PASSWD = os.environ.get('JQ_PASSWD')
