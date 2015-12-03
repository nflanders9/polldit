"""
subreddit.py
Nick Flanders

Classes for fetching information from subreddits
"""
import praw
import datetime
import utils
from configuration import *


class Subreddit:
    """Encapsulate functionality dealing with a single subreddit"""

    def __init__(self, name):
        """
        Initializes this SubredditComments object to the given subreddit name
        """
        name = "/r/" + name if name[:3] != "/r/" else name
        self.name = name
        self.subreddit = REDDIT.get_subreddit(name[3:])


    def __fetch_posts(self, begin=None, end=None):
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
        
        if DEBUG: print("Subreddit: {}\nNumber of posts in range: {}".format(
            self.name, len(posts)))

        return posts


    def __fetch_comments_on_posts(self, post_list):
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
            if DEBUG: print("Flattening: ", index)
            # returns a list of MoreComments objects that were not replaced
            remaining_more_comments = submission.replace_more_comments(limit=None)
            while len(remaining_more_comments) > 0:
                remaining_more_comments = submission.replace_more_comments()
            comments += list(praw.helpers.flatten_tree(submission.comments))
            if DEBUG: print(len(comments))

        if DEBUG: print("Number of comments: {}".format(len(comments)))
        
        return comments


    def fetch_text(self, begin=None, end=None):
        """
        Return a list of all text including comments and submissions that
        were posted to this subreddit in the given time interval and adds
        the text to the database

        args:
            begin:  the datetime object of the beginning of the interval
            end:    the datetime object of the end of the interval
        return:
            list of Posts added to the database
        """
        # set default parameters if none were passed to the method
        if end == None:
            end = datetime.datetime.now()
        if begin == None:
            begin = end - datetime.timedelta(hours=1)


        posts = self.fetch_posts(begin, end)
        comments = self.fetch_comments_on_posts(posts)
 
        posts_votes = [Text(post.title, post.ups, post.downs, utils.get_date(post)) for post in posts]
        comments_votes = [Text(comment.body, comment.ups, comment.downs, utils.get_date(comment)) for comment in comments]


        add_post = ("INSERT INTO posts "
              "(subreddit, post_datetime, post_text, upvotes, downvotes) "
              "VALUES (%(subreddit)s, time(%(post_datetime)s), %(post_text)s, %(upvotes)s, %(downvotes)s);")

        filtered = utils.filter_by_candidate(posts_votes + comments_votes)
        for candidate in filtered:
            text_list = filtered[candidate]
            for text in text_list:
                db_entry = {
                "subreddit": self.name,
                "post_datetime": text.datetime.strftime('%Y-%m-%d %H:%M:%S'),
                "post_text": text.content[:5000],
                "upvotes": text.upvotes,
                "downvotes": text.downvotes
                }
                CURSOR.execute(add_post, db_entry)

        DB.commit()
        return filtered


    def search(self, term):
        """
        Return a list of all the text as a result of searching this Subreddit for the
        given search term

        args:
            term:   the serach term
        return:
            list of Posts
        """
        self.subreddit.search(term)


class Text:
    """
    Represents text (a comment or a submission) with vote counts to reddit
    """
    def __init__(self, content, ups, downs, datetime):
        self.content = content
        self.upvotes = ups
        self.downvotes = downs
        self.datetime = datetime

    def __str__(self):
        return self.content