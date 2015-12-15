"""
corpus_compare.py

Nick Flanders

Compare the results of the original training corpus and the custom training corpus
when analyzing Reddit political sentiment and render the comparison as a graph in
the ouput svg file
"""
import sys
import warnings
import collections
import nltk
import nltk.classify.util
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import reddit_politics
from nltk.corpus import movie_reviews
import random
import pygal
from configuration import FILTER_LIST

ITERATIONS = 100
OUTPUT = "corpora_compasion.svg"

# process command line inputs
try:
    if len(sys.argv) > 1:
        for index, flag in enumerate(sys.argv):
            if flag == "-i":
                ITERATIONS = int(sys.argv[index + 1])
            elif flag == "-o":
                OUTPUT = sys.argv[index + 1]
                if OUTPUT[-4:] != ".svg":
                    OUTPUT += ".svg"
except:
    print("Syntax:  python corpus_compare.py [-i number_of_iterations] [-o output_svg]")



# control whether debugging messages are printed to the console
if len(sys.argv) > 1 and sys.argv[1] in ['-d', '-DEBUG']:
    DEBUG = True
warnings.filterwarnings("ignore")



def word_feats(words, filter_list):
    return dict([(word, True) for word in words if word not in filter_list and len(word) > 2])



# get all of the file IDs associated with the positive and negative entries in each corpus
reddit_negids = reddit_politics.fileids('neg')
reddit_posids = reddit_politics.fileids('pos')
movie_negids = movie_reviews.fileids('neg')
movie_posids = movie_reviews.fileids('pos')
 
# process the positive and negative features of each corpus
reddit_negfeats = [(word_feats(reddit_politics.words(fileids=[f]), FILTER_LIST), 'neg') for f in reddit_negids]
reddit_posfeats = [(word_feats(reddit_politics.words(fileids=[f]), FILTER_LIST), 'pos') for f in reddit_posids]
movie_negfeats = [(word_feats(movie_reviews.words(fileids=[f]), FILTER_LIST), 'neg') for f in movie_negids]
movie_posfeats = [(word_feats(movie_reviews.words(fileids=[f]), FILTER_LIST), 'pos') for f in movie_posids]

# list of tuples containing the accuracies of each training corpus
accuracies = []
for _ in range(ITERATIONS):
    # shuffle the reddit features each iteration so that a new subset of them is being used for testing
    random.shuffle(reddit_negfeats)
    random.shuffle(reddit_posfeats)

    # find the cutoff points in both the positive and negative feature sets to divide training and testing data
    negcutoff = int(len(reddit_negfeats) * 3 / 4)
    poscutoff = int(len(reddit_posfeats) * 3 / 4)

    # define the features to be used in testing for both of the corpora
    reddit_trainfeats = reddit_negfeats[:negcutoff] + reddit_posfeats[:poscutoff]
    movie_trainfeats = movie_posfeats + movie_negfeats

    # get the test features from the back ends of the reddit feature sets
    testfeats = reddit_negfeats[negcutoff:] + reddit_posfeats[poscutoff:]
 
    # test the accuracy of a classifier based on the reddit data
    reddit_classifier = NaiveBayesClassifier.train(reddit_trainfeats)
    reddit_accuracy = nltk.classify.util.accuracy(reddit_classifier, testfeats)
    print('Reddit Political Corpus Accuracy: ', reddit_accuracy)

    # test the accuract of a classifier based on the movie review data
    movie_classifier = NaiveBayesClassifier.train(movie_trainfeats)
    movie_accuracy = nltk.classify.util.accuracy(movie_classifier, testfeats)
    print('Movie Review Corpus Accuracy: ', movie_accuracy)

    # record the accuracies as a tuple
    accuracies.append((reddit_accuracy, movie_accuracy))


line_chart = pygal.Line(show_x_labels=False, range=(0, 1))
line_chart.title = "Accuracies of Training Corpora"
line_chart.x_labels = [str(num + 1) for num in range(ITERATIONS)]
line_chart.add("Reddit Corpus", [tup[0] for tup in accuracies])
line_chart.add("Movie Corpus", [tup[1] for tup in accuracies])
line_chart.render_to_file(OUTPUT)
