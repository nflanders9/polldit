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
import nltk
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer

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

# initialize CANDIDATES to a dictionary of list of candidate names where the
# keys are the last names of each candidate
CANDIDATE_LIST = config['candidates']
CANDIDATES = dict()
for name in CANDIDATE_LIST:
    CANDIDATES[name] = config['candidates'][name]


# PRAW always returns a ResourceWarning as Python garbage collection
# deletes the connection pool before processing it can be closed in 3.X
if not debug:
    warnings.filterwarnings("ignore")


class Text:
    """
    Represents text (a comment or a submission) with vote counts to reddit
    """
    def __init__(self, content, ups, downs):
        self.content = content
        self.ups = ups
        self.downs = downs

    def __str__(self):
        return self.content


class Subreddit:
    """Encapsulate functionality dealing with a single subreddit"""

    def __init__(self, name):
        """
        Initializes this SubredditComments object to the given subreddit name
        """
        name = "/r/" + name if name[:3] != "/r/" else name
        self.name = name
        self.subreddit = REDDIT.get_subreddit(name[3:])


    def posts(self, begin=None, end=None):
        """
        Return a list of all posts made between the given datetime objects.
        If no begin or end dates are given, it defaults to the last 24 hours

        args:
            begin: the early time bound for posts
            end:   the late time bound for posts
        return:
            list of Submission objects
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

        return posts


    def comments_on_posts(self, post_list):
        """
        Return a single list of all the comments on all posts in the
        given list of Submissions

        args:
            post_list:  list of Submission objects
        return:
            list of Comment objects
        """

        comments = []
        for index, submission in enumerate(post_list):
            if debug: print("Flattening: ", index)
            # returns a list of MoreComments objects that were not replaced
            remaining_more_comments = submission.replace_more_comments(limit=None)
            while len(remaining_more_comments) > 0:
                remaining_more_comments = submission.replace_more_comments()
            comments += list(praw.helpers.flatten_tree(submission.comments))
            print(len(comments))

        if debug: print("Number of comments: {}".format(len(comments)))
        
        return comments


    def get_text(self, begin=None, end=None):
        """
        Return a list of all text including comments and submissions that
        were posted to this subreddit in the given time interval

        args:
            begin:  the datetime object of the beginning of the interval
            end:    the datetime object of the end of the interval
        return:
            list of Posts
        """
        # set default parameters if none were passed to the method
        if end == None:
            end = datetime.datetime.now()
        if begin == None:
            begin = end - datetime.timedelta(hours=1)

        posts = self.posts(begin, end)
        comments = self.comments_on_posts(posts)

        posts_votes = [Text(post.title, post.ups, post.downs) for post in posts]
        comments_votes = [Text(comment.body, comment.ups, comment.downs) for comment in comments]

        return posts_votes + comments_votes


    def recent_comments(self, limit=None):
        """
        Return a list of recent comments from this subreddit since the given
        datetime object

        args:
            limit: the number of comment to return (up to 1000)
        return:
            list of Posts
        """
        comment_gen = self.subreddit.get_comments(limit=limit)
        comments = praw.helpers.flatten_tree(comment_gen)

        return [Post(comment.body, comment.ups, comment.downs) for comment in comments]


def filter_by_candidate(post_list, candidate):
    """
    Returns a list of posts from the given list that mention the name of
    the given candidate

    args:
        comment_list:   list of posts to filter
        candidate:      name of candidate to filter for
    return:
        list of comments mentioning the given candidate
    """
    names = CANDIDATES[candidate]
    output = []
    for post in post_list:
        for name in names:
            if name in post.content:
                output.append(post)
    return output


