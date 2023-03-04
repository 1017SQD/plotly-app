import dash_bootstrap_components as dbc
from dash import Input, Output, State, html
from dash_bootstrap_components._components.Container import Container

PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col([
                        html.Img(src=PLOTLY_LOGO, height="30px"),
                        dbc.NavbarBrand("Your Dashboard Analytics", className="ms-2")
                    ], 
                        width={'size':'auto'},
                    )
                ],
                align="center",
            ),
            dbc.Row([
                dbc.Col([
                    dbc.Nav(
                        dbc.NavItem(dbc.NavLink("Logout", href="/")),
                        navbar=True,
                    )
                ],
                    width={'size':'auto'},
                )
            ],
                align="center",
            )
        ],
        
        fluid=True,
    ),
    
    color="primary",
    dark=True,
)