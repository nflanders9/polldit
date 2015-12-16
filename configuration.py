"""
configuration.py
Nick Flanders

Loads configuration data from the config.yaml into a Python format
"""
import yaml
import utils
import praw


DEBUG = True
CONFIG_FILE = 'config.yaml'

# import configuration from config.yaml
with open(CONFIG_FILE, 'r') as f:
    config = yaml.load(f)

DB = config["db"]


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

ALL_NAMES = []
for candidate in CANDIDATES:
    ALL_NAMES += CANDIDATES[candidate]

FILTER_LIST = config["filter_list"]