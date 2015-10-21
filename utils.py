"""
utils.py
Nick Flanders

Utility functions for use in polldit.py
"""


def get_date(submission):
    """
    Return the date and time of submission of a post or a comment
    in YYYY-MM-DD HH:MM:SS format
    """
    return datetime.datetime.fromtimestamp(submission.created)


def safe_print(string):
    """
    If an error is found while printing due to an unsupported Unicode
    character, encode the string as an ASCII string and then print it out
    """
    try:
        print(string)
    except UnicodeEncodeError:
        print(str(string).encode("ascii", "ignore"))