"""
nltk_corpus_creator.py

Nick Flanders

Script to facilitate the efficient construction of a corpus using user-defined
data for use in training the NLTK sentiment analyzer

Usage:

    python nltk_corpus_creator.py <path to SQLite DB> <output directory for corpus>

"""

import sys
import os
import errno
import sqlite3

# process command line inputs
if len(sys.argv) != 3:
    print("syntax:   python nltk_corpus_creator.py <path to SQLite DB> <output directory for corpus>")
    sys.exit(1)

database = str(sys.argv[1])
corpus_dir = str(sys.argv[2])
pos_dir = corpus_dir + "/pos"
neg_dir = corpus_dir + "/neg"

# list used to strip names from text before adding to the corpus to avoid associations
candidates = ['bernie','sanders','bern','hillary','clinton',
'hrc','hilary',"martin","o'malley","omalley", "jeb", "bush",
"carson", "chris","christie", "cruz", "donald", "trump",
"carly", "fiorina", "kasich", "rand", "paul","marco", "rubio",
"rick", "santorum"]

# index of the column in the database to get text content from
column_index = 1

def mkdir_p(path):
    """
    Recursively create new directories (similar functionality to mkdir -p)
    """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def clear():
    """
    Clear the open console window
    """
    os.system('cls')


# create all of the paths needed for this corpus
if not os.path.exists(corpus_dir):
    mkdir_p(corpus_dir)
if not os.path.exists(pos_dir):
    os.mkdir(pos_dir)
if not os.path.exists(neg_dir):
    os.mkdir(neg_dir)


def sanitize(text):
    """
    Strip all mentions of candidates from the text to not associate the candidate's
    name in a positive or negative file
    """
    text = text.lower()
    for name in candidates:
        text = text.replace(name, "")
    return text



def make_file(text, sentiment, index):
    """
    Write a new file containing the given text to the output directory
    """
    filename = "/{}_reddit_{}.txt".format(sentiment, index)
    if sentiment == "pos":
        directory = pos_dir
    else:
        directory = neg_dir
    with open(directory + filename, 'w') as f:
        sanitized = sanitize(text)
        f.write(sanitized)




# read data to classify from the given SQLite database
db = sqlite3.connect(database)

pos_index = int(input("Starting positive index for the corpus: "))
neg_index = int(input("Starting negative index for the corpus: "))
mode = input("Enter a mode (\"submissions\" or \"comments\"): ")

if mode == "submissions":
    for text, in db.execute('select postTitle from submissions'):
        clear()
        sanitized_text = str(text.encode("ascii", "ignore"))
        designation = input(sanitized_text + ":  ")
        if designation in ['p', 'P', '+']:
            make_file(sanitized_text, "pos", pos_index)
            pos_index += 1
        elif designation in ['n', 'N', '-']:
            make_file(sanitized_text, "neg", neg_index)
            neg_index += 1

elif mode == "comments":
    for text, in db.execute('select body from comments'):
        clear()
        sanitized_text = str(text.encode("ascii", "ignore"))
        designation = input(sanitized_text + ":  ")
        if designation in ['p', 'P', '+']:
            make_file(sanitized_text, "pos", pos_index)
            pos_index += 1
        elif designation in ['n', 'N', '-']:
            make_file(sanitized_text, "neg", neg_index)
            neg_index += 1