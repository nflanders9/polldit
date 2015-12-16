# polldit
Predicting US presidential election poll results based on current reddit sentiment

This project relies on a custom sentiment analysis corpus called ```reddit_politics``` to
be used by NLTK. In the development of this project, the corpus was created using the
included script ```nltk_corpus_creator.py``` using a database of Reddit content created
using the "redditDataset.py" script. In order to add a custom corpus for use with
NLTK, the ```__init__.py``` file in the NLTK corpus module directory in a local Python
installation must be modified to include the following lines:
```
    reddit_politics = LazyCorpusLoader(
    'reddit_politics', CategorizedPlaintextCorpusReader,
    r'(?!\.).*\.txt', cat_pattern=r'(neg|pos)/.*')
```

Additionally, the custom corpus must be placed in a directory called ```reddit_politics```
somewhere on the NLTK path.