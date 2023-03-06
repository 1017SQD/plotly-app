import dash
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from apps import navigation
import pandas as pd
import authentification
import dash_bootstrap_components as dbc
from vaderSentiment_fr.vaderSentiment import SentimentIntensityAnalyzer
import re
import unicodedata
from nltk.tokenize import WordPunctTokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

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

# Function for polarity score
def polarity_score(tweet):
    SIA = SentimentIntensityAnalyzer()
    return SIA.polarity_scores(tweet)['compound']

# Function to get sentiment type
def sentimentvader(tweet):
    polarity = polarity_score(tweet)
    if polarity < 0:
        return "Négatif"
    elif polarity == 0:
        return "Neutre"
    else:
        return "Positif"

def status(screen_name, api):
    tweet_source = []
    year = []
    year_month = []
    tweets_txt = []
    nb_retweet = []
    nb_fav = []
    sentiment = []
    
    for status in get_all_tweets(screen_name, api):
        tweet_source.append(status.source)
        year.append(int(status.created_at.strftime("%Y")))
        year_month.append(status.created_at.strftime("%Y-%m"))
        tweets_txt.append(status.full_text)
        sentiment.append(sentimentvader(status.full_text))
        nb_retweet.append(status.retweet_count)
        nb_fav.append(status.favorite_count)
        
    dict_metrics = {'tweet_source': tweet_source, 'year': year,
          'tweets_txt':tweets_txt, 'nb_retweet':nb_retweet,
          'nb_favorite':nb_fav, 'year_month':year_month,
          'sentiment' : sentiment}
    
    df_metrics = pd.DataFrame(dict_metrics)
    return df_metrics

def cleaning_tweets(tweets):
    """
    Clean up a tweet by removing links, hashtags, mentions and emoticons.

    Parameters
    ----------
    tweet : str
        Tweet to clean up.

    Returns
    -------
    str
        Tweet cleaned up.
    """
    regex_pattern = re.compile(pattern="["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictograms
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "]+", flags=re.UNICODE)
    pattern = re.compile(r'(https?://)?(www\.)?(\w+\.)?(\w+)(\.\w+)(/.+)?')
    tweets = re.sub(regex_pattern, '', tweets)  # replaces the pattern with ''
    tweets = re.sub(pattern, '', tweets)
    tweets = re.sub(r'@[^\s]+', '', tweets)
    tweets = re.sub(r'#[^\s]+', '', tweets)
    # Removes special characters and links
    #tweets = re.sub(r'[^\w\s]', '', tweets)
    tweets = re.sub(r'https?://[A-Za-z0-9./]+', '', tweets)
    # Removes user mentions
    tweets = re.sub(r'@[A-Za-z0-9]+', '', tweets)

    token = WordPunctTokenizer()
    words = token.tokenize(tweets)
    result_words = [x for x in words]
    return " ".join(result_words)

def remove_emojis(tweets):
    text = cleaning_tweets(tweets)
    # Create an empty list to store the cleaned text
    cleaned_text = []

    # Scroll through each character of the text
    for character in text:
        # Use the `category` function of the `unicodedata` library to get the Unicode category of the character
        character_category = unicodedata.category(character)
        # If the character's Unicode category is not "So" (Symbol, Other), add the character to the clean text list
        if character_category != "So":
            cleaned_text.append(character)

    # Join the characters in the cleaned text list into a string and return it
    return "".join(cleaned_text)

def process_tweets(tweets):
    """
    Processes tweets by removing empty words.

    Parameters
    ----------
    tweets : list of str
        List of tweets to process.

    Returns
    -------
    list of str
        List of processed tweets.
    """
    with open("french_stopwords.txt", "r", encoding="utf-8") as stopwords_file:
        stopwords = []
        for line in stopwords_file:
            word = line.split("|")[0].strip()
            stopwords.append(word)

    cleaned_tweets = []
    for tweet in tweets.lower().split():
        if (tweet not in stopwords) and (len(tweet) > 1):
            cleaned_tweets.append(remove_emojis(tweet))
                      
    return cleaned_tweets
        
df_metrics = status(screen_name, api)
df_fig1 = df_metrics.groupby(['tweet_source', 'year'])['tweet_source'].count().reset_index(name='nb_source')
df_fig2 = df_metrics.groupby(['year_month', 'year'])['nb_retweet'].sum().reset_index(name='nb_rt')
df_fig3 = df_metrics.groupby(['year_month', 'year'])['nb_favorite'].sum().reset_index(name='nb_fav')

# using the functions to get the polarity and sentiment
# df_metrics['polarity'] = df_metrics['tweets_txt'].apply(polarity)
# df_metrics['sentiment'] = df_metrics['polarity'].apply(sentimenttextblob)
df_fig4 = df_metrics.groupby(['sentiment', 'year'])['sentiment'].count().reset_index(name='nb_sent')

df_fig5 = df_metrics.groupby(['year_month', 'year'])['tweets_txt'].count().reset_index(name='nb_tweet')

df_fig6 = df_metrics.copy()

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
                    value=[df_metrics['year'].max()-2,  df_metrics['year'].max()-1],
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
        
        html.Br(),
        
        dbc.Row([
            dbc.Col([
                dbc.Card(dcc.Graph(id='nb_tweet')),
            ], xs=12, sm=12, md=12, lg=6, xl=6),
            
            dbc.Col([
                dbc.Card(dcc.Graph(id='wordcloud')),
            ], xs=12, sm=12, md=12, lg=6, xl=6),
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card(dcc.Graph(id='wc_pos')),
            ], xs=12, sm=12, md=12, lg=6, xl=6),
            
            dbc.Col([
                dbc.Card(dcc.Graph(id='wc_neg')),
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
    Output('wc_pos', 'figure'),
    Output('wc_neg', 'figure'),
    Input('year-slider', 'value'))
def update_figure(selected_year):
    filtered_df = df_fig1[(df_fig1["year"] >= selected_year[0]) & (df_fig1["year"] < selected_year[1])]
    
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
    
    filtered_df2 = df_fig2[(df_fig2["year"] >= selected_year[0]) & (df_fig2["year"] < selected_year[1])]
    fig2 = px.line(filtered_df2, x='year_month', y='nb_rt', template='ggplot2')
    fig2.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                       xaxis_title=None, yaxis_title=None, title='Retweets by Month')
    
    filtered_df3 = df_fig3[(df_fig3["year"] >= selected_year[0]) & (df_fig3["year"] < selected_year[1])]
    fig3 = px.line(filtered_df3, x='year_month', y='nb_fav', template='ggplot2')
    fig3.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                       xaxis_title=None, yaxis_title=None, title='Likes by Month')
    
    filtered_df4 = df_fig4[(df_fig4["year"] >= selected_year[0]) & (df_fig4["year"] < selected_year[1])]
    
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
    
    filtered_df5 = df_fig5[(df_fig5["year"] >= selected_year[0]) & (df_fig5["year"] < selected_year[1])]
    fig5 = px.bar(filtered_df5, x='year_month', y='nb_tweet', template='ggplot2')
    fig5.update_yaxes(tickangle=45)
    fig5.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                       xaxis_title=None, yaxis_title=None, title='Tweets by Month')
    
    tweets_filtered = ' '.join(list(df_fig6[(df_fig6["year"] >= selected_year[0]) & (df_fig6["year"] < selected_year[1])].tweets_txt))
    tweets_procced = ' '.join(process_tweets(remove_emojis(tweets_filtered)))
    
    my_wordcloud = WordCloud(
        background_color='white',
        height=275,
        max_words = 100
    ).generate(tweets_procced)

    fig_wordcloud = px.imshow(my_wordcloud, template='ggplot2')
    fig_wordcloud.update_layout(margin=dict(l=0, r=0, t=15, b=15))
    fig_wordcloud.update_xaxes(visible=False)
    fig_wordcloud.update_yaxes(visible=False)
    
    tweets_filtered_pos = ' '.join(list(df_metrics[(df_metrics["year"] >= selected_year[0]) &
                                            (df_metrics["year"] < selected_year[1]) &
                                            (df_metrics["sentiment"] == "Positif")].tweets_txt))
    
    tweets_procced_pos = ' '.join(process_tweets(remove_emojis(tweets_filtered_pos)))
    
    my_wordcloud_pos = WordCloud(
        background_color='white',
        height=275,
        max_words = 100
    ).generate(tweets_procced_pos)

    fig_wordcloud_pos = px.imshow(my_wordcloud_pos, template='ggplot2')
    fig_wordcloud_pos.update_layout(margin=dict(l=0, r=0, t=15, b=15))
    fig_wordcloud_pos.update_xaxes(visible=False)
    fig_wordcloud_pos.update_yaxes(visible=False)
    
    tweets_filtered_neg = ' '.join(list(df_metrics[(df_metrics["year"] >= selected_year[0]) &
                                            (df_metrics["year"] < selected_year[1]) &
                                            (df_metrics["sentiment"] == "Négatif")].tweets_txt))
    
    tweets_procced_neg = ' '.join(process_tweets(remove_emojis(tweets_filtered_neg)))
    
    my_wordcloud_neg = WordCloud(
        background_color='white',
        height=275,
        max_words = 100
    ).generate(tweets_procced_neg)

    fig_wordcloud_neg = px.imshow(my_wordcloud_neg, template='ggplot2')
    fig_wordcloud_neg.update_layout(margin=dict(l=0, r=0, t=15, b=15))
    fig_wordcloud_neg.update_xaxes(visible=False)
    fig_wordcloud_neg.update_yaxes(visible=False)
    

    
    return fig, fig2, fig3, fig4, fig5, fig_wordcloud, fig_wordcloud_pos, fig_wordcloud_neg