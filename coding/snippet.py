import os
from bs4 import BeautifulSoup
import time
import math
import re

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
    print ("finish building document list")


def create_query_list(listpath, querydic):
    '''

    :param listpath: string file location
    :param querydic: dic{int queryid: [splitted query content]}
    :return:
    '''
    f = open(listpath, 'r')
    content = f.read()
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
    print (len(querydic))
    print ("finish create query dictionary")


def queryparser(query):
    '''

    :param query: string
    :return:
    '''
    stoplist = create_stopword_list("../test-collection/common_words.txt")
    puncs = [',', '.', '(', ')', '[', ']', '\n', '?', ';', '-', ':']
    for punc in puncs:
        query = query.replace(punc, ' ')
    query = query.lower()
    temp = query.split()
    query = []
    for item in temp:
        if item not in stoplist:
            query.append(item)
    return query


def docparser(docdic):
    res = {}
    for d_id, content in docdic.items():
        res[d_id] = [(match.group(0), match.start(0)) for match in re.finditer('\\w+', content)]
    return res


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
        content = re.sub('\\s+', ' ', content)
        docdic[doc] = content

    print ("finish parsing")


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

def create_result_list(filePath, Result_dic):
    with open(filePath, 'r') as f:
        for line in f:
            if not line.startswith('------') and not line.startswith('results for') and line:
                items = line.split()
                q_id = int(items[0])
                file = items[2]
                doc_id = int(file[file.find('-') + 1 :])
                if q_id not in Result_dic:
                    Result_dic[q_id] = []
                Result_dic[q_id].append(doc_id)


def generate_snippet(query, doc, terms):
    windowsize = 10
    is_in_snippet = [False] * len(terms)
    seq = [int(term in query) for (term, pos) in terms]
    scores = [ sum(seq[left: left+windowsize])**2 / windowsize for left in range(len(seq)-windowsize)]
    ranking = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    for i, score in ranking[:10]:
        for j in range(windowsize):
            is_in_snippet[i+j] = True
    res = ""
    write_dot = True
    for i, f in enumerate(is_in_snippet):
        if f:
            if seq[i]:
                res += '<b>'
                res += doc[terms[i][1]:terms[i+1][1]]
                res += '</b>'
            else:
                res += doc[terms[i][1]:terms[i+1][1]]
            write_dot = True
        else:
            if write_dot:
                res += '... '
                write_dot = False
    return res

def generate_snippet_list(Que_dic, Result_dic, Doc_dic, term_dic, Snippet_dic):
    for q_id, results in Result_dic.items():
        query = Que_dic[q_id]
        for d_id in results:
            doc = Doc_dic[d_id]
            terms = term_dic[d_id]
            if q_id not in Snippet_dic:
                Snippet_dic[q_id] = {}
            Snippet_dic[q_id][d_id] = generate_snippet(query, doc, terms)


def write_snippet(Snippet_dic):
    with open('results/snippet_BM25.txt', 'w') as f:
        for qid, docs in Snippet_dic.items():
            f.write("Query "+str(qid)+'\n')
            for did, snippet in docs.items():
                f.write("CACM-" + str(did)+"\n")
                f.write(snippet+'\n')
                f.write('\n')
            f.write("------------------------------------------" + '\n')


if __name__ == '__main__':
    QueryPath = "../test-collection/cacm.query.txt"
    FilePath = "../test-collection/cacm"
    ResultPath = "results/task1/BM25.txt"
    Que_dic = {}
    Doc_dic = {}
    Result_dic = {}
    Snippet_dic = {}


    create_query_list(QueryPath, Que_dic)
    creat_doc_list(FilePath, Doc_dic)
    create_result_list(ResultPath, Result_dic)

    parser(Doc_dic)
    term_dic = docparser(Doc_dic)


    generate_snippet_list(Que_dic, Result_dic, Doc_dic, term_dic, Snippet_dic)

    write_snippet(Snippet_dic)
