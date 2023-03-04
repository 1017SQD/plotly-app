# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_bootstrap_components as dbc
from dash import html


app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
                suppress_callback_exceptions=True,
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )

server = app.server

app.layout = html.Div(children=[
    dash.page_container
    ])

if __name__ == '__main__':
    app.run_server(debug=True)