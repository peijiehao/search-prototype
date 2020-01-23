import os
from bs4 import BeautifulSoup


def get_lucene_result(filepath):
    f = open(filepath, 'r')
    resultlist = []
    ranklist = []
    print
    for line in f.readlines():
        if line.find("results") > -1:
            if len(ranklist) > 0:
                resultlist.append(ranklist)
            ranklist = []
            continue
        docid = int(line[line.find('-') + 1 : line.rfind('r') - 1])
        ranklist.append([docid, 0])
    resultlist.append(ranklist)
    f.close()
    return resultlist


def creat_doc_list(docpath, docdic):
    '''

    :param docpath: string, path to open document folder
    :param doclist: [string title, list [string content]]
    :return:
    '''
    files = os.listdir(docpath)
    for file in files:
        f = open(docpath + '/' + file, 'r')
        html = f.read()
        soup = BeautifulSoup(html, features="html.parser")
        docid = int(file[file.find('-') + 1 : file.find('.')])
        docdic[docid] = soup
        f.close()
    print "finish building document list"


def create_stem_doc_list(docpath, docdic):
    '''

    :param docpath: string file location
    :param docdic: dic[int documentid : list splitted content]
    :return:
    '''
    f = open(docpath, 'r')
    content = f.read()
    f.close()
    content = content.replace(" pm ", " jb ")
    content = content.replace(" am ", " jb ")
    while (1):
        index1 = content.find("#")
        index2 = content.find('\n')
        index3 = content.find("jb")
        docid = int(content[index1 + 1: index2])
        docdic[docid] = content[index2 + 1: index3].split()
        index4 = content[index1 + 1:].find("#")
        if index4 < 0:
            break
        else:
            temp = content[index4 + 1:]
            content = temp
    print "finish building stemmed document list"


def create_rel_list(listpath, reldic):
    '''

    :param listpath: string file location
    :param reldic: dic{int queryid: [document id]}
    :return:
    '''
    f = open(listpath, 'r')
    for line in f.readlines():
        queryid = int(line[:2])
        if queryid not in reldic:
            reldic[queryid] = []
        reldic[queryid].append(int(line[line.find('-') + 1 : line.rfind('1') - 1]))
    f.close()
    print "finish creating relevance dictionary"


def create_query_list(listpath, querydic):
    '''

    :param listpath: string file location
    :param querydic: dic{int queryid: [splitted query content]}
    :return:
    '''
    f = open(listpath, 'r')
    content = f.read()
    f.close()
    while content.find("<DOC>") > -1:
        index1 = content.find("<DOCNO>")
        index2 = content.find("</DOCNO>")
        index3 = content.find("</DOC>")
        queryid = int(content[index1 + 7 : index2 - 1])
        querydic[queryid] = []
        query = content[index2 + 8 : index3 - 1]
        querydic[queryid] = queryparser(query)
        temp = content[index3 + 6 :]
        content = temp
    print "finish create query dictionary"


def parser(docdic):
    '''

    :param docdic: document dictionary
    :return:
    '''
    tags = ['html', 'pre']
    for doc in docdic:
        for tag in tags:
            if len(docdic[doc].findAll(tag)) > 0:
                for match in docdic[doc].findAll(tag):
                    match.replaceWithChildren()
        docdic[doc] = str(docdic[doc])
        content = docdic[doc][: docdic[doc].rfind("M") + 1]
        docdic[doc] = queryparser(content)
    print "finish parsing"


def queryparser(query):
    '''

    :param query: string
    :return:
    '''
    stoplist = create_stopword_list("/Users/peggy/Desktop/information retrieval/prj/test-collection/common_words.txt")
    puncs = [',', '.', '(', ')', '[', ']', '\n', '?', ';', '-', ':']
    for punc in puncs:
        query = query.replace(punc, ' ')
    query = query.lower()
    query = query.split()
    temp = []
    for item in query:
        if item not in stoplist:
            temp.append(item)
    query = temp
    return query



def create_stopword_list(filepath):
    '''

    :param filepath: string file location
    :return:
    '''
    f = open(filepath, 'r')
    stoplist = f.read()
    stoplist.split()
    f.close()
    return stoplist