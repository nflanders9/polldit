__author__ = 'Ari Morcos'

from requests import HTTPError
import praw
import datetime
import time
import itertools
import sys
import os
import sqlite3
import re
import shutil



def createDataset(r, subreddits, startDate=(datetime.datetime.now()-datetime.timedelta(days=7)).strftime('%y%m%d%H%M%S'),
                  endDate=datetime.datetime.now().strftime('%y%m%d%H%M%S'), nCommentsPerSubmission=100, dbName='reddit',
                  dbPath=None, fineScale=12, nPostsPerFineScale=200, keywords=[]):
    """
    :param r: reddit object
    :param subreddits: list of subreddits to grab
    :param startDate: start date in format yymmddHHMMSS
    :param endDate: end date in format yymmddHHMMSS
    :param nCommentsPerSubmission: number of comments to grab per submission. Default is 100.
    :param dbName: base of database name
    :param fineScale: scale of database in hours
    :param nPostsPerFineScale: number of posts per fine scale
    :return:
    """

    # initialize database
    dbObj = RedditDB(dbName=dbName, dbPath=dbPath)

    # loop through each subreddit
    for sub in subreddits:

        print('Processing subreddit: ', str(sub.title.encode('utf-8'))[2:-1])

        # get submissions within the date range
        matchingPosts = getAllPostsWithinRangeFineScale(sub, startDate=startDate, endDate=endDate, fineScale=fineScale,
                                                        nPostsPer=nPostsPerFineScale)

        # loop through each post and get top comments
        for post in matchingPosts:

            # if there are keywords to match against, check the post content
            addedPost = False
            if len(keywords) > 0:
                for keyword in keywords:
                    if keyword in post.title.lower():
                        addedPost = True
                        print('Processing post: ', str(post.title.encode('utf-8'))[2:-1])
                        dbObj.saveSubmission(post)
                        break
                    
            else:
                print('Processing post: ', str(post.title.encode('utf-8'))[2:-1])
                dbObj.saveSubmission(post)
                addedPost = True

            # get comments if the post was added
            if addedPost:
                numTries = 0
                gotComments = False
                while not gotComments and numTries < 10:
                    try:
                        comments = getCommentsFromSubmission(post, nCommentsPerSubmission)
                        gotComments = True
                    except HTTPError:
                        time.sleep(2)
                        numTries += 1

                # save comment data for comments which have not been deleted if the comment matches any of the given keywords
                for comment in comments:
                    if isinstance(comment, praw.objects.Comment) and comment.author is not None:
                        if keywords != None:
                            for keyword in keywords:
                                if keyword in comment.body:
                                    dbObj.saveCommentData(comment)
                                    break
                        else:
                            dbObj.saveCommentData(comment)

    dbObj.closeConnection()
    print('\nData collection complete!')


def getSubreddits(r, subredditNames):
    """
    :param r: reddit object
    :param subredditNames: list of subreddit names to retrieve
    :return: generator object of subreddit objects
    """

    for sub in subredditNames:
        yield r.get_subreddit(sub.lower())


def getRecentSubmissions(subreddit, dateRange):

    try:
        # perform an empty search to get all submissions within date range
        searchResult = subreddit.search('', period=dateRange, limit=None)
    except HTTPError:
        time.sleep(2)
        searchResult = getRecentSubmissions(subreddit, dateRange)

    # return search result
    return searchResult


def getCommentsFromSubmission(submission, nCommentsPerSubmission):

    # get comment list
    flatComments = praw.helpers.flatten_tree(submission.comments)

    # filter list and return
    return flatComments[:nCommentsPerSubmission]


def getAllPostsWithinRangeFineScale(subreddit, startDate, endDate, fineScale=12, nPostsPer=1000):
    """
    Grabs posts using fine scale to grab maximum number
    :param fineScale: scale in hours. Default is 12.
    :param subreddit: subreddit object
    :param startDate: start date in format yymmdd
    :param endDate: end date in format yymmdd
    :param nPostsPer: number of posts per unit
    :return:
    """

    # create datetime object for each date
    startDateObject = datetime.datetime.strptime(startDate, "%y%m%d%H%M%S")
    endDateObject = datetime.datetime.strptime(endDate, "%y%m%d%H%M%S")

    # get posts
    posts = []
    tempStart = startDateObject
    while True:

        # get temporary end date
        tempEnd = tempStart + datetime.timedelta(hours=fineScale)

        # check if tempEnd is after than endDateObject
        if (tempEnd - endDateObject) > datetime.timedelta(0, 0, 0):
            # set tempEnd to be endDateObject
            tempEnd = endDateObject

        # break if start is after end
        if (tempStart - tempEnd) > datetime.timedelta(0, 0, 0):
            break

        # convert to strings
        tempStartStr = tempStart.strftime('%y%m%d%H%M%S')
        tempEndStr = tempEnd.strftime('%y%m%d%H%M%S')

        # get posts within range
        tempPosts = getPostsWithinRange(subreddit, tempStartStr, tempEndStr, nPosts=nPostsPer)

        # combine with posts
        posts = itertools.chain(posts, tempPosts)

        # iterate on start date
        tempStart = tempEnd + datetime.timedelta(seconds=1)

    # return
    return posts


def getPostsWithinRange(subreddit, startDate, endDate, nPosts=1000):
    """
    :param subreddit: subreddit object
    :param startDate: start date in format yymmddHHMMSS
    :param endDate: end date in format yymmddHHMMSS
    :return: generator object of posts
    """
    # convert dates to unix time format
    startDate = time.mktime(datetime.datetime.strptime(startDate, "%y%m%d%H%M%S").timetuple())
    endDate = time.mktime(datetime.datetime.strptime(endDate, "%y%m%d%H%M%S").timetuple())

    # generate timestamp search term
    searchTerm = 'timestamp:' + str(startDate)[:-2] + '..' + str(endDate)[:-2]

    # get posts
    try:
        posts = subreddit.search(searchTerm, sort='top', syntax='cloudsearch', limit=nPosts)
    except HTTPError:
        time.sleep(2)
        posts = getPostsWithinRange(subreddit, startDate, endDate, nPosts=nPosts)

    return posts




###########################################################################################



class RedditDB:
    """
    Class for interfacing with a database for reddit data sets
    """

    def __init__(self, dbName='reddit', dbPath=None):
        self.__dbName = dbName
        self.__dbPath = dbPath
        self.__c = None  # initialized in initialize database
        self.__initializeDatabase()

    def __getDatabasePath(self):
        """
        :return: full absolute database path
        """

        if self.__dbPath is None:
            userPath = os.path.expanduser('~')
            basePath = os.path.abspath(os.path.join(userPath, 'Databases'))
        else:
            basePath = self.__dbPath

        databasePath = os.path.abspath(os.path.join(basePath, self.__dbName + '.db'))

        # make directory if it doesn't exist
        if not os.path.exists(basePath):
            os.makedirs(basePath)
        return databasePath

    def __initializeDatabase(self):
        """
        Initializes a database connection called 'reddit.db'
        :return: cursor object
        """

        dbPath = self.__getDatabasePath()
        self.__dbObj = sqlite3.connect(dbPath)
        self.__c = self.__dbObj.cursor()

        # get list of tables
        tableList = self.__c.execute("Select name from sqlite_master where type = 'table' ")

        # check if comments exist in tableList
        commentsPresent = any(['comments' == item[0] for item in [row for row in list(tableList)]])

        if not commentsPresent:
            self.__createTables()

    def __createTables(self):
        # create comments table
        self.__c.execute('Create TABLE comments (date, user, body, comScore, postID)')

        # create submissions table
        self.__c.execute('Create TABLE submissions (postID, postTitle, postBody, postScore, postDate, '
                         'subredditName, subredditID)')

    def saveCommentData(self, comment):
        """
        :param comment: comment object
        :return: void
        """

        # extract relevant fields
        commentDate = datetime.datetime.fromtimestamp(comment.created_utc)
        commentDateStr = commentDate.strftime('%Y%m%d%H%M%S')
        userName = comment.author.name
        body = comment.body
        submissionID = comment._submission.name
        score = comment.score

        # save data
        self.__c.execute('Insert into comments VALUES (?, ?, ?, ?, ?)', [commentDateStr, userName, body, score, submissionID])
        self.__c.connection.commit()

    def saveSubmission(self, post):
        """
        :param post: post object
        :return: void
        """

        # extract relevant fields
        submissionID = post.name
        submissionTitle = post.title
        submissionDate = datetime.datetime.fromtimestamp(post.created_utc)
        submissionDateStr = submissionDate.strftime('%Y%m%d%H%M%S')
        subredditID = post.subreddit.name
        subredditName = post.subreddit.display_name
        score = post.score
        if post.is_self:
            body = post.selftext
        else:
            body = post.url

        # save data
        self.__c.execute('Insert into submissions VALUES (?, ?, ?, ?, ?, ?, ?)', [submissionID, submissionTitle, body,
                                                                                  score, submissionDateStr,
                                                                                  subredditName, subredditID])
        self.__c.connection.commit()

    def getSubreddits(self):
        """ Extracts a list of distinct subreddits """

        # execute query
        self.__c.execute('select distinct subredditName '
                         'from submissions '
                         'group by subredditName '
                         'order by count(*) desc')

        # grab results
        rawOut = self.__c.fetchall()

        return [item[0] for item in rawOut]

    def getSubredditCommentText(self, subreddit):
        """ Grabs all comment text and concatenates from a given subreddit """

        # execute query
        self.__c.execute("select body "
                         "from comments "
                         "where postID in "
                         "  (select postID "
                         "   from submissions "
                         "   where subredditName = ?)", [subreddit])

        # get comments
        rawComments = self.__c.fetchall()

        return [item[0] for item in rawComments]

    def closeConnection(self):
        self.__dbObj.close()


def mergeDBs(path, dbName='mergedDB'):
    """
    Merges multiple databases into one large database
    :param path: path to folder containing databases. Will merge all of these databases
    :param dbName: Name of the merged database. Default is mergedDB.
    """

    # get list of database objects in path
    allFiles = os.listdir(path)

    # get db files
    dbFiles = [dbFile for dbFile in allFiles if re.match(r'.*\.db', dbFile) is not None]

    # get path of first file and new database object
    source = os.path.abspath(os.path.join(path, dbFiles[0]))
    destination = os.path.abspath(os.path.join(path, dbName + '.db'))

    # check if destination file exists
    if os.path.isfile(destination):
        userInput = raw_input('Destination file already exists. Continue (y/n): ')
        if userInput.lower() == 'n':
            print('Ending merge.')
            return
        elif userInput.lower() != 'y':
            print('Cannot process input. Ending merge.')
            return

    # copy file
    shutil.copyfile(source, destination)

    # create sql object
    dbObj = sqlite3.connect(destination)
    c = dbObj.cursor()

    # loop through each database, attach, and merge
    for dbFile in dbFiles[1:]:

        # create query
        sqlQuery = "attach '" + os.path.abspath(os.path.join(path, dbFile)) + """' as toMerge;
                    INSERT into comments select * from toMerge.comments;
                    INSERT into submissions select * from toMerge.submissions;
                    detach toMerge;"""

        # execute and commit
        c.executescript(sqlQuery)
        dbObj.commit()

    print('Merge complete!')
