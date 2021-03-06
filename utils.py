"""
utils.py
Nick Flanders

Utility functions for use in polldit.py
"""
import sys
import math
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

    # filter out any comments containing this line since it is a comment that has been
    # deleted from reddit
    removed_string = "has been removed for the following reason"

    for post in post_list:
        for candidate in CANDIDATES:
            names = CANDIDATES[candidate]
            for name in names:
                if name in post.content and removed_string not in post.content:
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

def update_progress(completed, message=None, width=40):
    """
    Display a progress bar for a task that is the given percent completed
    :param completed:   the ratio of the task completed (con the closed interval [0, 1])
    :param message:     the preceding message to display in front of the progress bar
    :param width:       the width of the progress bar
    """
    if message is None:
        message_str = ""
    else:
        message_str = message
    done_width = int(math.ceil(completed * width))
    sys.stdout.write("\r" + message_str + " [{}]".format(" " * (width - 1)) + " " + str(int(completed * 100)) + "%")
    sys.stdout.write("\r" + message_str + " " + '\u2588' * (done_width + 1))