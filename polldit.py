"""
polldit.py

Nick Flanders

Predicting poll results for the 2016 US Presidential election
based on sentiment in Reddit comments and posts
"""

import praw
import yaml


#####################
#     CONSTANTS     #
#####################

CONFIG_FILE = 'config.yaml'

# import configuration from config.yaml
with open(CONFIG_FILE, 'r') as f:
    config = yaml.load(f)


USER_AGENT = config['user_agent']
REDDIT = praw.Reddit(USER_AGENT)
SUBREDDITS = config['subreddits']
REDDIT_URL = config['reddit_url']




"""
politics = reddit.get_subreddit('neu')
pol_subs = politics.get_hot(limit=2)
submissions = 
for sub in pol_subs:
    for comment in sub:
            print("comment: ")
            print(comment)

#comment_tree = politics.get_comments()
#comments = praw.helpers.flatten_tree(comment_tree)
#print(str(comments[0]))
"""