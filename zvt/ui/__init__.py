# -*- coding: utf-8 -*-
import os

import dash

assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets'))

zvt_app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}], assets_folder=assets_path
)

zvt_app.config.suppress_callback_exceptions = True

server = zvt_app.server
