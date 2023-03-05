import dash
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from apps import navigation
import pandas as pd
import authentification
import dash_bootstrap_components as dbc
from textblob import TextBlob
from textblob_fr import PatternTagger, PatternAnalyzer

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
                               exclude_replies=False,
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
                                   exclude_replies=False,
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

def status(screen_name, api):
    tweet_source = []
    year = []
    year_month = []
    tweets_txt = []
    nb_retweet = []
    nb_fav = []
    
    for status in get_all_tweets(screen_name, api):
        tweet_source.append(status.source)
        year.append(int(status.created_at.strftime("%Y")))
        year_month.append(status.created_at.strftime("%Y-%m"))
        tweets_txt.append(status.full_text)
        nb_retweet.append(status.retweet_count)
        nb_fav.append(status.favorite_count)
        
    dict_metrics = {'tweet_source': tweet_source, 'year': year,
          'tweets_txt':tweets_txt, 'nb_retweet':nb_retweet,
          'nb_favorite':nb_fav, 'year_month':year_month}
    
    df_metrics = pd.DataFrame(dict_metrics)
    return df_metrics

df_metrics = status(screen_name, api)

# Function for polarity score
def polarity(tweet):
    return TextBlob(tweet, pos_tagger=PatternTagger(),
                    analyzer=PatternAnalyzer()).sentiment[0]

# Function to get sentiment type
def sentimenttextblob(polarity):
    if polarity < 0:
        return "Négatif"
    elif polarity == 0:
        return "Neutre"
    else:
        return "Positif"

df_fig1 = df_metrics.groupby(['tweet_source', 'year'])['tweet_source'].count().reset_index(name='nb_source')
df_fig2 = df_metrics.groupby(['year_month', 'year'])['nb_retweet'].sum().reset_index(name='nb_rt')
df_fig3 = df_metrics.groupby(['year_month', 'year'])['nb_favorite'].sum().reset_index(name='nb_fav')

# using the functions to get the polarity and sentiment
df_metrics['polarity'] = df_metrics['tweets_txt'].apply(polarity)
df_metrics['sentiment'] = df_metrics['polarity'].apply(sentimenttextblob)
df_fig4 = df_metrics.groupby(['sentiment', 'year'])['sentiment'].count().reset_index(name='nb_sent')

df_fig5 = df_metrics.groupby(['year_month', 'year'])['tweets_txt'].count().reset_index(name='nb_tweet')

dash.register_page(__name__, path='/', title="Plotly App", description="Twitter Analytics")

layout = html.Div([
    navigation.navbar,
    html.Br(),
    dbc.Container([
        
        dbc.Row([
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("3500", className="card-title"),
                    html.P("Nombre de tweets", className="card-text")
                    ]),
                color="primary", inverse=True
                )),
            
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("7500", className="card-title"),
                    html.P("Nombre de retweets", className="card-text")
                    ]),
                color="secondary", inverse=True
                )),
            
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("976", className="card-title"),
                    html.P("Nombre de likes", className="card-text")
                    ]),
                color="info", inverse=True
                )),
            
            dbc.Col(dbc.Card(
                dbc.CardBody([
                    html.H5("974", className="card-title"),
                    html.P("Nombre inconnu", className="card-text")
                    ]),
                color="warning", inverse=True
            )),
            
            ],
                className="mb-4",
            ),
        
        dbc.Row([
            dbc.Col([
                dbc.Card(dcc.Graph(id='example-graph')),
                    dcc.RangeSlider(
                    df_metrics['year'].min(),
                    df_metrics['year'].max(),
                    step=1,
                    value=[df_metrics['year'].min()+1,  df_metrics['year'].max()-1],
                    marks={str(year): str(year) for year in df_metrics['year'].unique()},
                    id='year-slider')
            ], xs=12, sm=12, md=12, lg=6, xl=6),
            
            dbc.Col([
                dbc.Card(dcc.Graph(id='nb_rt_tweet')),
                ], xs=12, sm=12, md=12, lg=6, xl=6)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card(dcc.Graph(id='nb_fav_tweet')),
            ], xs=12, sm=12, md=12, lg=6, xl=6),
            
            dbc.Col([
                dbc.Card(dcc.Graph(id='nb_sent')),
            ], xs=12, sm=12, md=12, lg=6, xl=6)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card(dcc.Graph(id='nb_tweet')),
            ], xs=12, sm=12, md=12, lg=6, xl=6),
            
            dbc.Col([
                dbc.Card(dcc.Graph(id='wordcloud')),
            ], xs=12, sm=12, md=12, lg=6, xl=6),
        ]),
    ],
        fluid=True,
    )
])

@dash.callback(
    Output('example-graph', 'figure'),
    Output('nb_rt_tweet', 'figure'),
    Output('nb_fav_tweet', 'figure'),
    Output('nb_sent', 'figure'),
    Output('nb_tweet', 'figure'),
    Output('wordcloud', 'figure'),
    Input('year-slider', 'value'))
def update_figure(selected_year):
    filtered_df = df_fig1[(df_fig1["year"] >= selected_year[0]) & (df_fig1["year"] <= selected_year[1])]
    
    fig = px.pie(data_frame=filtered_df, names="tweet_source",
                 values="nb_source", hole=.5)

    fig.update_layout(transition_duration=500,
                       legend=dict(
                           orientation="h",
                           yanchor="bottom",
                           y=1,
                           xanchor="right",
                           x=1), 
                       margin=dict(l=20, r=20, t=30, b=20))
    
    filtered_df2 = df_fig2[(df_fig2["year"] >= selected_year[0]) & (df_fig2["year"] <= selected_year[1])]
    fig2 = px.line(filtered_df2, x='year_month', y='nb_rt', template='ggplot2')
    fig2.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                       xaxis_title=None, yaxis_title=None)
    
    filtered_df3 = df_fig3[(df_fig3["year"] >= selected_year[0]) & (df_fig3["year"] <= selected_year[1])]
    fig3 = px.line(filtered_df3, x='year_month', y='nb_fav', template='ggplot2')
    fig3.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                       xaxis_title=None, yaxis_title=None)
    
    filtered_df4 = df_fig4[(df_fig4["year"] >= selected_year[0]) & (df_fig4["year"] <= selected_year[1])]
    
    fig4 = px.pie(data_frame=filtered_df4, names='sentiment', values='nb_sent', hole=.5)

    fig4.update_layout(transition_duration=500,
                       legend=dict(
                           orientation="h",
                           yanchor="bottom",
                           y=1.02,
                           xanchor="right",
                           x=1),
                       margin=dict(l=20, r=20, t=30, b=20),
                       xaxis_title=None,
                       yaxis_title=None)
    
    filtered_df5 = df_fig5[(df_fig5["year"] >= selected_year[0]) & (df_fig5["year"] <= selected_year[1])]
    fig5 = px.bar(filtered_df5, x='year_month', y='nb_tweet', template='ggplot2')
    fig5.update_yaxes(tickangle=45)
    fig5.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                       xaxis_title=None, yaxis_title=None)

    
    return fig, fig2, fig3, fig4, fig5