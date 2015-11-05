"""
utils.py
Nick Flanders

Utility functions for use in polldit.py
"""
import datetime
import collections
from configuration import *

def get_date(submission):
    """
    Return the date and time of submission of a post or a comment
    in YYYY-MM-DD HH:MM:SS format
    """
    return datetime.datetime.fromtimestamp(submission.created)

def filter_by_candidate(post_list):
    """
    Returns a dictionary mapping a candidate's name to the list of posts
    that they are mentioned in in the given list of posts

    args:
        comment_list:   list of posts to filter
    return:
        dictionary formatted like: {<candidate_name>:[<post1>, <post2>, ...], ...}
    """
    output = collections.defaultdict(list)

    for post in post_list:
        for candidate in CANDIDATES:
            names = CANDIDATES[candidate]
            for name in names:
                if name in post.content:
                    output[candidate].append(post)
    return output


def safe_print(string):
    """
    If an error is found while printing due to an unsupported Unicode
    character, encode the string as an ASCII string and then print it out
    """
    try:
        print(string)
    except UnicodeEncodeError:
        print(str(string).encode("ascii", "ignore"))