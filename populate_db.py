"""
populate_db.py
Nick Flanders

Populate the MySQL database containing a record of all reddit text mentioning
candidates in a given time frame
"""
import datetime
from subreddit import *
from configuration import *

def populate(start, end):
    """
    Populate the MySQL database with all Reddit information between the two
    given datetimes.
    """
    subreddits = [Subreddit(sub_name) for sub_name in SUBREDDITS]
    cur_time = start
    while cur_time < end:
        for subreddit in subreddits:
            subreddit.fetch_text(cur_time, cur_time + datetime.timedelta(hours=1))
        cur_time += datetime.timedelta(hours=1)
