"""
polldit.py

Nick Flanders

Predicting poll results for the 2016 US Presidential election
based on sentiment in Reddit comments and posts
"""
import sys
import os
import warnings
import collections
import utils
import nltk
import nltk.classify.util
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import reddit_politics
import sqlite3
from configuration import *
import random
import pygal
import re
import math
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
import webbrowser

DEBUG = False
# control whether debugging messages are printed to the console
if len(sys.argv) > 1 and sys.argv[1] in ['-d', '-DEBUG']:
    DEBUG = True
warnings.filterwarnings("ignore")
os.system('cls' if os.name == 'nt' else 'clear')
print()


def word_feats(words, filter_list):
    return dict([(word, True) for word in words if word not in filter_list and len(word) > 2])


def create_classifier(iterations=100):
    """
    Return the classifier that did the best at classifying a subset of the data
    after training for the given number of iterations

    :param iterations: number of iterations to test on
    :return:    tuple: (classifier, accuracy of classifier) 
    """
    negids = reddit_politics.fileids('neg')
    posids = reddit_politics.fileids('pos')

    negfeats = [(word_feats(reddit_politics.words(fileids=[f]), FILTER_LIST), 'neg') for f in negids]
    posfeats = [(word_feats(reddit_politics.words(fileids=[f]), FILTER_LIST), 'pos') for f in posids]
    
    # track the most accurate classifier so far
    best_classifier = None
    highest_accuracy = 0
    for iter_num in range(iterations):
        # randomly shuffle the feature sets to get new subsets to test and train on
        random.shuffle(negfeats)
        random.shuffle(posfeats)
    
        negcutoff = int(len(negfeats) * 3 / 4)
        poscutoff = int(len(posfeats) * 3 / 4)
    
        trainfeats = negfeats[:negcutoff] + posfeats[:poscutoff]#negfeats[:negcutoff] + posfeats[:poscutoff]
        testfeats = negfeats[negcutoff:] + posfeats[poscutoff:]#negfeats[negcutoff:] + posfeats[poscutoff:]

        if DEBUG: print('Train on %d instances, test on %d instances.\n' % (len(trainfeats), len(testfeats)))
     
        # train the classifier on the training features and determine its accuracy
        classifier = NaiveBayesClassifier.train(trainfeats)
        accuracy = nltk.classify.util.accuracy(classifier, testfeats)

        if DEBUG: print('\nAccuracy:', accuracy)

        # if this classifier outperformed all before it, track it and its accuracy
        if accuracy > highest_accuracy:
            highest_accuracy = accuracy
            best_classifier = classifier
        utils.update_progress(iter_num / iterations, message="Testing Classifiers")
    sys.stdout.write("\n\n")
    return (classifier, highest_accuracy)


def get_posts(start_date, end_date):
    """
    Return a dictionary of candidate names mapped to the tuples containing the score and
    the text of a piece of Reddit content

    :param start_date: the integer start date of the time interval in YYYYMMDDHHMMSS format
    :param end_date: the integer end date of the time interval in YYYYMMDDHHMMSS format 
    """
    connection = sqlite3.connect(DB)
    db = connection.cursor()
    
    results = []
    comments = db.execute("SELECT * FROM COMMENTS WHERE date >= ? AND date <= ?", (start_date, end_date))
    
    # keys are candidates, values are lists of tuples with score and content
    posts = dict()
    
    for date, user, body, score, post_id in comments:
        for candidate in CANDIDATES:
            for name in CANDIDATES[candidate]:
                # generate a regular expression that ensures that the name isn't part of another word
                regex = r"^.* " + name
                if re.match(regex, body.lower()):
                    if candidate not in posts:
                        posts[candidate] = []
                    posts[candidate].append((score, body.lower()))
    
    submissions = db.execute("SELECT * FROM SUBMISSIONS WHERE postDate >= ? AND postDate <= ?", (start_date, end_date))
    
    for postID, title, body, score, date, subreddit_name, subreddit_id in submissions:
        for candidate in CANDIDATES:
            for name in CANDIDATES[candidate]:
                # generate a regular expression that ensures that the name isn't part of another word
                regex = r"^.* " + name
                if re.match(regex, (title + "\n" + body).lower()):
                    if candidate not in posts:
                        posts[candidate] = []
                    posts[candidate].append((score, (title + "\n" + body).lower()))

    connection.close()
    return posts


def classify(classifier, text, score):
    """
    Returns a numeric classification value of the text using the given NLTK Classifier and
    taking into account the score associated with the given text

    :param classifier:  the NLTK Classifier to use for sentiment analysis
    :param text:        the text content to analyze
    :return:            a numeric value representing the overall sentiment of this Reddit content
    """
    feature = word_feats(text.split(), [])
    probabilities = classifier.prob_classify(feature)
    label = probabilities.max()
    pos_prob = probabilities.prob("pos")
    neg_prob = probabilities.prob("neg")
    if score >= 0 and pos_prob >= 0.5:
        value = math.log1p(score + 1)
    elif score < 0 and neg_prob >= 0.5:
        value = 0 - math.log1p(0 - score + 1)
    elif score >= 0 and neg_prob >= 0.5:
        value = 0 - math.log1p(score + 1)
    else:
        value = math.log1p(0 - score + 1)
    return value + 1



# entry point into the program
if __name__ == "__main__":

    # generate a classifier to use for sentiment analysis
    classifier, accuracy = create_classifier()
    print("Best classifier accuracy: ", accuracy)
    if DEBUG: classifier.show_most_informative_features(n=10)
    
    start_date = int(input("\nEnter the start datetime (YYYYMMDDHHMMSS): "))
    end_date = int(input("Enter the end datetime (YYYYMMDDHHMMSS): "))
    
    posts = get_posts(start_date, end_date)
    
    # dictionary containing candidates mapped to lists of sentiment values for that candidate
    sentiments = dict()
    totals = dict()
    overall_total = 0
    num_candidates = len(list(posts.keys()))
    current = 1
    for candidate in posts:
        sentiments[candidate] = []
        totals[candidate] = 0
        for score, text in posts[candidate]:
            sentiments[candidate].append(classify(classifier, text, score))
            totals[candidate] += 1
            overall_total += 1
        utils.update_progress(current / num_candidates, message=candidate)
        current += 1
    # clear the progress bars for the candidates
    sys.stdout.write("\r" + " " * 70 + "\n")
    
    # normalize the values to 0
    lowest = 0
    for candidate in sentiments:
        avg = sum(sentiments[candidate]) / overall_total
        if avg < lowest:
            lowest = avg

    # display sentiment values for each candidate to the console
    print("\nRelative Sentiment Values:")
    print("(normalized to 0, higher is more positive)\n")
    for candidate in sentiments:
        print("\t", "{0: <12}".format(candidate), (sum(sentiments[candidate]) / overall_total) - lowest)

    # ensure that an output directory exists
    if not os.path.exists("output"):
        os.mkdir("output")

    # display a graph that has only the Democrats relative to each other
    democrat_chart = pygal.HorizontalBar(show_x_labels=False, width=1000, height=400)
    democrat_chart.title = "Reddit Democratic Candidate Sentiment"
    DEMOCRATS.sort()
    for candidate in DEMOCRATS:
        if candidate not in sentiments:
            sentiments[candidate] = [0]
            # avoid division by 0 errors if the candidate was not found 
            totals[candidate] = 1

        # since these graphs are relative only, add a slight offset to each of them so that the candidate
        # with the least approval does not appear to be missing from the graph
        democrat_chart.add(candidate, (sum(sentiments[candidate]) / overall_total) - lowest + 0.01)

    # save the chart to a file and display the svg with the default browser
    democrat_chart.render_to_file("output/democrats.svg")
    webbrowser.open_new('file://' + os.path.realpath("output/democrats.svg"))


    # display a graph that has only the Republicans relative to each other
    republican_chart = pygal.HorizontalBar(show_x_labels=False)
    republican_chart.title = "Reddit Republican Candidate Sentiment"
    REPUBLICANS.sort()
    for candidate in REPUBLICANS:
        if candidate not in sentiments:
            sentiments[candidate] = [0]
            totals[candidate] = 1
        republican_chart.add(candidate, (sum(sentiments[candidate]) / overall_total) - lowest + 0.01)
    republican_chart.render_to_file("output/republicans.svg")
    webbrowser.open_new_tab('file://' + os.path.realpath("output/republicans.svg"))


    # display a graph that combines the data for candidates from both parties
    all_chart = pygal.HorizontalBar(show_x_labels=False)
    all_chart.title = "Reddit Presidential Candidate Sentiment"
    all_candidates = DEMOCRATS + REPUBLICANS
    for candidate in all_candidates:
        all_chart.add(candidate, (sum(sentiments[candidate]) / overall_total) - lowest + 0.01)
    all_chart.render_to_file("output/all_candidates.svg")
    webbrowser.open_new_tab('file://' + os.path.realpath("output/all_candidates.svg"))