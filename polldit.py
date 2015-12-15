"""
polldit.py

Nick Flanders

Predicting poll results for the 2016 US Presidential election
based on sentiment in Reddit comments and posts
"""
import sys
import warnings
import collections
import utils
import nltk
import nltk.classify.util
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import reddit_politics
import sqlite3
from subreddit import *
from configuration import *
import random
import pygal
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer

DEBUG = False
# control whether debugging messages are printed to the console
if len(sys.argv) > 1 and sys.argv[1] in ['-d', '-DEBUG']:
    DEBUG = True
warnings.filterwarnings("ignore")


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
    for _ in range(100):
        # randomly shuffle the feature sets to get new subsets to test and train on
        random.shuffle(negfeats)
        random.shuffle(posfeats)
    
        negcutoff = int(len(negfeats) * 3 / 4)
        poscutoff = int(len(posfeats) * 3 / 4)
    
        trainfeats = negfeats[:negcutoff] + posfeats[:poscutoff]
        testfeats = negfeats[negcutoff:] + posfeats[poscutoff:]

        if DEBUG: print('Train on %d instances, test on %d instances.\n' % (len(trainfeats), len(testfeats)))
     
        # train the classifier on the training features and determine its accuracy
        classifier = NaiveBayesClassifier.train(trainfeats)
        accuracy = nltk.classify.util.accuracy(classifier, testfeats)

        if DEBUG: print('\nAccuracy:', accuracy)

        # if this classifier outperformed all before it, track it and its accuracy
        if accuracy > highest_accuracy:
            highest_accuracy = accuracy
            best_classifier = classifier
    return (classifier, highest_accuracy)


classifier, accuracy = create_classifier()
print("Accuracy: ", accuracy)
classifier.show_most_informative_features(n=10)
