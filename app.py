# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import tweepy
import authentification

screen_name = "1O17SQD"
TWEET_MODE = 'extended'
api = authentification.credentials()

def get_tweets(screen_name, api):
    """
    Retrieves tweets from the specified user using the specified Twitter API.

    Parameters
    ----------
    screen_name : str
        Screen name of the user whose tweets are to be retrieved.
    api: tweepy.API
        Twitter API object used to access the user's tweets.

    Returns
    -------
    list of tweepy.models.Status
        List of the user's tweets.
    """
    tweets = api.user_timeline(screen_name=screen_name,
                               # 200 is the maximum number allowed
                               count=200,
                               exclude_replies=True,
                               include_rts=False,
                               # Necessary to keep the full text
                               # otherwise only the first 140 words are extracted
                               tweet_mode=TWEET_MODE
                               )
    return tweets

def get_all_tweets(screen_name, api):
    """
    Retrieves all tweets from the specified user using the specified Twitter API.

    Parameters
    ----------
    screen_name : str
        Screen name of the user whose tweets are to be retrieved.
    api: tweepy.API
        Twitter API object used to access the user's tweets.

    Returns
    -------
    list of tweepy.models.Status
        List of all the user's tweets.
    """
    tweets = get_tweets(screen_name, api)
    all_tweets = []
    all_tweets.extend(tweets)
    oldest_id = tweets[-1].id
    while True:
        tweets = api.user_timeline(screen_name=screen_name,
                                   # 200 is the maximum number allowed
                                   count=200,
                                   exclude_replies=True,
                                   include_rts=False,
                                   max_id=oldest_id - 1,
                                   # Necessary to keep the full text
                                   # otherwise only the first 140 words are extracted
                                   tweet_mode=TWEET_MODE
                                   )
        if not len(tweets):
            break
        oldest_id = tweets[-1].id
        all_tweets.extend(tweets)

    return all_tweets

def tweet_source(screen_name, api):
    tweet_source = []
    tweet_created_year = []
    
    for status in get_all_tweets(screen_name, api):
        tweet_source.append(status.source)
        tweet_created_year.append(int(status.created_at.strftime("%Y")))
        
    df = {'tweet_source': tweet_source, 'tweet_created_year': tweet_created_year}
    df = pd.DataFrame(df)
    df = df.groupby(['tweet_source', 'tweet_created_year'])['tweet_source'].count().reset_index(name='count')
    
    return df

df_source = tweet_source(screen_name, api)

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
           meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
           )

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

df2 = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')

#fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1('Hello Dash',
                    className='text-center'),
            
            html.P('Dash: A web application framework for your data.',
                   className='text-center mb-4')
            ], width=12),
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='example-graph'),
                dcc.RangeSlider(
                df_source['tweet_created_year'].min(),
                df_source['tweet_created_year'].max(),
                step=1,
                value=[df_source['tweet_created_year'].min()+1,  df_source['tweet_created_year'].max()-1],
                marks={str(year): str(year) for year in df_source['tweet_created_year'].unique()},
                id='year-slider')
        ], xs=12, sm=12, md=12, lg=5, xl=5),
        
        dbc.Col([
            dcc.Graph(id='life-exp-vs-gdp'),
            dcc.Slider(
                df2['year'].min(),
                df2['year'].max(),
                step=None,
                value=df2['year'].min(),
                marks={str(year): str(year) for year in df2['year'].unique()},
                id='year-slider2')
            ], xs=12, sm=12, md=12, lg=6, xl=6)
    ])
    
])

@app.callback(
    Output('example-graph', 'figure'),
    Input('year-slider', 'value'))
def update_figure(selected_year):
    filtered_df = df_source[(df_source["tweet_created_year"] >= selected_year[0]) & (df_source["tweet_created_year"] <= selected_year[1])]
    
    fig = px.pie(data_frame=filtered_df, names="tweet_source", values="count", hole=.5)

    fig.update_layout(transition_duration=500,
                       legend=dict(
                           orientation="h",
                           yanchor="bottom",
                           y=1,
                           xanchor="right",
                           x=1))
    return fig

@app.callback(
    Output('life-exp-vs-gdp', 'figure'),
    Input('year-slider2', 'value'))
def update_figure2(selected_year):
    filtered_df = df2[df2.year == selected_year]

    fig2 = px.scatter(filtered_df, x="gdpPercap", y="lifeExp",
                     size="pop", color="continent", hover_name="country",
                     log_x=True, size_max=55)

    fig2.update_layout(transition_duration=500,
                       legend=dict(
                           title="",
                           orientation="h",
                           yanchor="bottom",
                           y=0.9,
                           xanchor="right",
                           x=1))

    return fig2

if __name__ == '__main__':
    app.run_server(debug=True)