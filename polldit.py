"""
polldit.py

Nick Flanders

Predicting poll results for the 2016 US Presidential election
based on sentiment in Reddit comments and posts
"""
import warnings
import collections
import utils
import sys
import nltk
import mysql.connector
from subreddit import *
import configuration
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer

# control whether debugging messages are printed to the console
if len(sys.argv) > 1 and sys.argv[1] in ['-d', '-DEBUG']:
    DEBUG = True



# PRAW always returns a ResourceWarning as Python garbage collection
# deletes the connection pool before processing it can be closed in 3.X
if not DEBUG:
    warnings.filterwarnings("ignore")


test = Subreddit("android")
posts = test.fetch_posts()
print([item.text for item in posts])
