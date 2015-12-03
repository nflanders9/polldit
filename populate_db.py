#!/usr/bin/env python3
"""
populate_db.py
Nick Flanders

Create databases for every subreddit in the presidential list for the specified time period
"""
import datetime
import re
import sys
import os
import warnings
from subreddit import *
from configuration import *
from reddit_dataset import redditDB
from reddit_dataset import redditDataset


warnings.filterwarnings("ignore")

if len(sys.argv) != 4:
    print("syntax:   python populate_db.py start_date(YYMMDDHHMMSS) end_date(YYMMDDHHMMSS) database_path")
    sys.exit(1)

# extract the name of the db from the file path
start = str(sys.argv[1])
end = str(sys.argv[2])
match = re.match(r".*[/\\](.+)\.db", "/" + str(sys.argv[3]))

if not match:
    print("invalid database path (must end in .db)")
    sys.exit(1)
name = match.group(1)

path = str(sys.argv[3]).strip(name).strip('.db')
if len(path) == 0:
    path = os.getcwd()


# generate the Reddit database
subs = redditDataset.getSubreddits(REDDIT, SUBREDDITS)
redditDataset.createDataset(
    REDDIT, subs, startDate=start, endDate=end,
    dbName=name, dbPath=path, fineScale=4, keywords=ALL_NAMES)

