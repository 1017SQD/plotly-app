# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 00:09:13 2022

@author: 18017952
"""
from dotenv import load_dotenv   #for python-dotenv method
import tweepy
import os 

def credentials():
    load_dotenv()  # take environment variables from .env.
    
    consumer_key = os.getenv('TWITTER_API_KEY')
    consumer_secret = os.getenv('TWITTER_API_SECRET_KEY')

    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    return tweepy.API(auth, wait_on_rate_limit=True)