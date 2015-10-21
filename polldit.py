"""
polldit.py

Nick Flanders

Predicting poll results for the 2016 US Presidential election
based on sentiment in Reddit comments and posts
"""

import praw
import yaml
import warnings
import datetime
import utils
import sys

# control whether debugging messages are printed to the console
debug = False
if len(sys.argv) > 1 and sys.argv[1] in ['-d', '-debug']:
    debug = True


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


# PRAW always returns a ResourceWarning as Python garbage collection
# deletes the connection pool before processing it can be closed in 3.X
if not debug:
    warnings.filterwarnings("ignore")


class Subreddit:
    """Encapsulate functionality dealing with a single subreddit"""

    def __init__(self, name):
        """
        Initializes this SubredditComments object to the given subreddit name
        """
        name = "/r/" + name if name[:3] != "/r/" else name
        self.name = name
        self.subreddit = REDDIT.get_subreddit(name[3:])

    def comments(self, begin=None, end=None):
        """
        Return a list of all comments on posts made between the given
        datetime objects. If no begin or end dates are given, it defaults
        to the last 24 hours

        args:
            begin: the early time bound for comments
            end:   the late time bound for comments
        """
        # set default parameters if none were passed to the method
        if end == None:
            end = datetime.datetime.now()
        if begin == None:
            begin = end - datetime.timedelta(hours=1)

        posts = list(self.subreddit.search('timestamp:' + str(begin.timestamp()).split('.')[0] +
            '..' + str(end.timestamp()).split('.')[0], syntax='cloudsearch', limit=None))
        
        if debug: print("Subreddit: {}\nNumber of posts in range: {}".format(
            self.name, len(posts)))

        comments = []
        for submission in posts:
            comments += list(praw.helpers.flatten_tree(submission.comments))

        if debug: print("Number of comments: {}".format(len(comments)))
        
        return comments

