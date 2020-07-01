# -*- coding: utf-8 -*-

import dash
app = dash.Dash(
    __name__, serve_locally=False, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

app.config.suppress_callback_exceptions = True
