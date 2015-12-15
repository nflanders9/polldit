"""
configuration.py
Nick Flanders

Loads configuration data from the config.yaml into a Python format
"""
import yaml
import mysql.connector
import utils

import praw


DEBUG = True
CONFIG_FILE = 'config.yaml'

# import configuration from config.yaml
with open(CONFIG_FILE, 'r') as f:
    config = yaml.load(f)

db_config = config["db"]


USER_AGENT = config['user_agent']
REDDIT = praw.Reddit(USER_AGENT)
SUBREDDITS = config['subreddits']
REDDIT_URL = config['reddit_url']

DB = mysql.connector.connect(
    user=db_config["user"],
    password=db_config["password"],
    host=db_config["address"],
    database=db_config["name"])

CURSOR = DB.cursor()


# initialize CANDIDATES to a dictionary of list of candidate names where the
# keys are the last names of each candidate
CANDIDATE_LIST = config['candidates']
CANDIDATES = dict()
for name in CANDIDATE_LIST:
    CANDIDATES[name] = config['candidates'][name]

ALL_NAMES = []
for candidate in CANDIDATES:
    ALL_NAMES += CANDIDATES[candidate]

FILTER_LIST = config["filter_list"]