import os
from bs4 import BeautifulSoup
import math
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as pl
import collections
import numpy
import preparation as pre



def inverted_list(docdic, inv_list):
    '''

    :param docdic: document dictionary
    :param inv_list: dic{string term: [[document id, frequency]]}
    :return:
    '''
    for doc in docdic:
        for token in docdic[doc]:
            if token in inv_list and doc == inv_list[token][len(inv_list[token]) - 1][0]:
                continue
            count = 0
            for item in docdic[doc]:
                if item == token:
                    count += 1
            list = [doc, count]
            if token not in inv_list:
                inv_list[token] = []
            inv_list[token].append(list)
    print "finish inverted list"


def BM25(inv_list, docdic, queryid, querydic, rellist, k1, k2, b):
    print "calculating BM25 document rank"
    ranklist = []
    query = querydic[queryid]
    if queryid in rellist:
        R = float(len(rellist[queryid]))
    else:
        R = 0.0
    N = float(len(docdic))
    length = 0
    for doc in docdic:
        length += len(docdic[doc])
    avdl = float(length / N)
    for doc in docdic:
        K = float(k1 * (float(1 - b) + b * float(len(docdic[doc])) / avdl))
        docrank = 0
        for term in query:
            qfi = 0
            for terms in query:
                if terms == term:
                    qfi += 1
            qfi = float(qfi)
            ri = 0.0
            if queryid in rellist:
                for name in rellist[queryid]:
                    if term in docdic[name]:
                        ri += 1
                ri = float(ri)
            if term in inv_list:
                ni = float(len(inv_list[term]))
                fi = 0.0
                for name in inv_list[term]:
                    if name[0] == doc:
                        fi = float(name[1])
            else:
                ni = 0.0
                fi = 0.0
            temp1 = (ri + 0.5) / (R - ri + 0.5)
            temp2 = (ni - ri + 0.5) / (N - ni - R + ri + 0.5)
            temp3 = (k1 + 1.0) * fi / (K + fi)
            temp4 = (k2 + 1.0) * qfi / (k2 + qfi)
            docrank += math.log(temp1 / temp2) * temp3 * temp4
        ranklist.append([doc, docrank])
    rank_sort(ranklist)
    ranklist = ranklist[:100]
    write_rank_list(ranklist, queryid, "BM25")
    return ranklist



def cal_tfidf_weight(docdic, inv_list, tfidf_weight_dict):
    '''
    build document tf-idf weight metrics
    store in tfidf_weight_dict
    :return:
    '''
    tfidf_weight = {}
    for doc_id in docdic:
        tfidf_weight[doc_id] = []
    N = len(docdic)
    for term in inv_list.keys():
        curt_inv_list = inv_list[term]
        nk = len(curt_inv_list)
        idfk = math.log(float(N) / float(nk))
        curt_inv_dict = dict(curt_inv_list)

        for doc_id in docdic:
            temp_weight = idfk
            if doc_id in curt_inv_dict:
                temp_weight *= (float(math.log(curt_inv_dict[doc_id])) + 1.0)
            tfidf_weight[doc_id].append([term, temp_weight])
    print "finish sub weight"

    for doc_id in tfidf_weight.keys():
        dominator = 0.0
        doc_term_weight_list = tfidf_weight[doc_id]
        for curt_doc_term_weight_list in doc_term_weight_list:
            dominator += math.pow(curt_doc_term_weight_list[1], 2)
        dominator = math.sqrt(dominator)
        for curt_doc_term_weight_list in doc_term_weight_list:
            curt_doc_term_weight_list[1] /= dominator
    print "finish matrix"

    for doc_id in tfidf_weight.keys():
        tfidf_weight_dict[doc_id] = dict(tfidf_weight[doc_id])
    print "finish to dict"



def tfidf_rank_doc(tfidf_weight_dict, query_id, querydic):
    print "calculating tfidf rank"
    doc_rank = {}
    query_str_list = querydic[query_id]
    query_term_freq = dict(collections.Counter(query_str_list))
    dominator = 0.0
    for term in query_term_freq.keys():
        dominator += math.pow(query_term_freq[term], 2)
    dominator = math.sqrt(dominator)
    for term in query_term_freq.keys():
        query_term_freq[term] /= dominator
    for doc_id in tfidf_weight_dict.keys():
        query_weight_list = []
        doc_weight_list = []
        for query_term in query_term_freq.keys():
            query_weight_list.append(query_term_freq[query_term])
            if query_term in tfidf_weight_dict[doc_id]:
                doc_weight_list.append(tfidf_weight_dict[doc_id][query_term])
            else:
                doc_weight_list.append(0.0)
        doc_rank[doc_id] = numpy.dot(query_weight_list, doc_weight_list) \
                           / (numpy.linalg.norm(query_weight_list) * numpy.linalg.norm(doc_weight_list))
    doc_rank = sorted(doc_rank.items(), key=lambda item: item[1], reverse=True)
    i = 1
    ranklist = []
    for curt_doc in doc_rank:
        if i > 100:
            break
        ranklist.append([curt_doc[0], curt_doc[1]])
        i += 1
    write_rank_list(ranklist, query_id, "TF_IDF")
    return ranklist



def JelinekM(inv_list, docdic, queryid, querydic, lamda):
    '''

    :param inv_list:
    :param docdic:
    :param queryid:
    :param querydic:
    :param lamda:
    :return:
    '''
    print "calculating JM document rank"
    ranklist = []
    query = querydic[queryid]
    C = 0
    for doc in docdic:
        C += len(docdic[doc])
    for doc in docdic:
        docrank = 0
        D = float(len(docdic[doc]))
        for term in query:
            fqi = 0.0
            cqi = 0
            if term not in inv_list:
                continue
            else:
                for name in inv_list[term]:
                    cqi += name[1]
                    if name[0] == doc:
                        fqi = float(name[1])
            cqi = float(cqi)
            temp1 = float(1.0 - lamda) * fqi / D
            temp2 = lamda * cqi / C
            docrank += math.log(temp1 + temp2)
        ranklist.append([doc, docrank])
    rank_sort(ranklist)
    ranklist = ranklist[:100]
    write_rank_list(ranklist, queryid, "JelineKM")
    return ranklist


def rank_sort(ranklist):
    '''
    sort rank list basig on doc rank
    :param ranklist: [int docid, int score]
    :return:
    '''
    ranklist.sort(key = lambda item:item[1] , reverse = True)


def write_rank_list(ranklist, queryid, model):
    '''
    store rank list
    :param ranklist:
    :param queryid:
    :param model: string model's name
    :return:
    '''
    f = open("/Users/peggy/Desktop/information retrieval/prj/" + model + "stemmed.txt", 'a')
    f.write("results for query " + str(queryid))
    f.write('\n')
    count = 1
    for item in ranklist:
        f.write(str(queryid) + " " + "Q0 " + "CACM-" + str(item[0]) + " rank: " + str(item[1]))
        count += 1
        f.write('\n')
    f.write("------------------------------------------" + '\n')
    f.close()


def PRF(inv_list, docdic, queryid, querydic, stoplist, rellist):
    '''
    pseudo relevant feedback
    :param inv_list:
    :param docdic:
    :param queryid:
    :param querydic:
    :param lamda:
    :param stoplist: [string stopword]
    :param rellist:
    :param k1:
    :param k2:
    :param b:
    :return:
    '''
    ranklist = BM25(inv_list, docdic, queryid, querydic, rellist, 1.2, 0.0, 0.75)
    termdic = {}
    for doc in ranklist[:10]:
        for term in docdic[doc[0]]:
            if term in stoplist:
                continue
            if term not in termdic:
                termdic[term] = 1
            else:
                termdic[term] += 1
    termlist = [key for key, value in sorted(termdic.items(), key = lambda item:item[1], reverse = True)[:10]]
    ranklist = BM25(inv_list, docdic, 0, {0: querydic[queryid] + termlist}, rellist, 1.2, 2.0, 0.75)
    write_rank_list(ranklist, queryid, "PRF BM25_0 + BM25_2")
    return ranklist



def evaluation(filepath, ranklist, reldic, queryid):
    print "evaluating"
    count = 1
    recall = []
    reldocs = 0
    map = 0.0
    mrr = 0.0
    precision = []
    R = len(reldic[queryid])
    for item in ranklist:
        if item[0] in reldic[queryid]:
            reldocs += 1
            if mrr == 0.0:
                mrr = 1.0 / float(count)
        recall.append(float(reldocs) / float(R))
        precision.append(float(reldocs) / float(count))
        if item[0] in reldic[queryid]:
            map += float(reldocs) / float(count)
        count += 1
    if reldocs != 0:
        map = map / float(reldocs)
    aver = average_recall_precision(recall, precision)
    f = open(filepath, 'a')
    f.write("recall and precision for query " + str(queryid))
    f.write('\n')
    print map
    print mrr
    for i in range(len(recall)):
        f.write(str(recall[i]) + " | " + str(precision[i]) + '\n')
    f.write("--------------------------------" + '\n' + '\n' )
    f.close()
    return aver, map, mrr, precision[4], precision[19]


def average_recall_precision(recall, precision):
    avpre = [0.0] * 11
    for i in range(len(recall)):
        if recall[i] >= 0:
            avpre[0] = max(avpre[0], precision[i])
        if recall[i] >= 0.1:
            avpre[1] = max(avpre[1], precision[i])
        if recall[i] >= 0.2:
            avpre[2] = max(avpre[2], precision[i])
        if recall[i] >= 0.3:
            avpre[3] = max(avpre[3], precision[i])
        if recall[i] >= 0.4:
            avpre[4] = max(avpre[4], precision[i])
        if recall[i] >= 0.5:
            avpre[5] = max(avpre[5], precision[i])
        if recall[i] >= 0.6:
            avpre[6] = max(avpre[6], precision[i])
        if recall[i] >= 0.7:
            avpre[7] = max(avpre[7], precision[i])
        if recall[i] >= 0.8:
            avpre[8] = max(avpre[8], precision[i])
        if recall[i] >= 0.9:
            avpre[9] = max(avpre[9], precision[i])
        if recall[i] >= 1.0:
            avpre[10] = max(avpre[10], precision[i])
    # print avpre
    return avpre


def method_evaluation(Que_dic, Doc_dic, Inv_list, Rel_dic, stoplist, lucenelist):
    # map = 0
    # mrr = 0
    # pre5 = 0
    # pre20 = 0
    # averpre = [0.0] * 11
    # query = 1

    for query in Que_dic:
    # for Rank_list in lucenelist:
    #     print query
    #     Rank_list = BM25(Inv_list, Doc_dic, query, Que_dic, Rel_dic, 1.2, 0.0, 0.75)
    #     Rank_list = JelinekM(Inv_list, Doc_dic, query, Que_dic, 0.35)
        # Rank_list = PRF(Inv_list, Doc_dic, query, Que_dic, stoplist, Rel_dic)
        Rank_list = tfidf_rank_doc(tfidf_weight_dict, query, Que_dic)

        # if query in Rel_dic:
        #     print query
        #     aver, ap, rr, p5, p20 = evaluation("/Users/peggy/Desktop/information retrieval/prj/tfidf_evaluation.txt",
        #                          Rank_list, Rel_dic, query)
        #     for i in range(11):
        #         averpre[i] += aver[i]
        #
        # map += ap
        # mrr += rr
        # pre5 += p5
        # pre20 += p20
        # query += 1

    # size = float(len(Rel_dic))
    #
    # f = open("/Users/peggy/Desktop/information retrieval/prj/average_precision.txt", 'a')
    # f.write("tfidf" + '\n')
    # for item in averpre:
    #     f.write(str(item/size) + '  ')
    # f.write('\n')
    # f.close()
    #
    # map = map / size
    # mrr = mrr / size
    # pre5 = pre5 / size
    # pre20 = pre20 / size
    # f = open("/Users/peggy/Desktop/information retrieval/prj/tfidf_evaluation.txt", 'a')
    # f.write("map: " + str(map) + '\n' + "mrr: " + str(mrr) + '\n' + "P@5: " + str(pre5) + '\n' + "P@20: " + str(pre20))
    # f.close()


def plot_recall_precision(filename):
    pl.figure()
    pl.xlabel("recall")
    pl.ylabel("precision")
    recall = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    f = open(filename, 'r')
    lines = f.readlines()
    for i in range(0, len(lines), 2):
        print i
        title = lines[i][:len(lines[i]) - 1]
        print title
        avpre = []
        for num in lines[i + 1].split():
            print num
            avpre.append(float(num))
        pl.plot(recall, avpre, label = title)
    pl.legend(loc = "upper right")
    pl.title("average recall precision curve for eight runs")
    pl.savefig("/Users/peggy/Desktop/information retrieval/prj/recall-precision_curve.png")



if __name__ == '__main__':
    FilePath = "/Users/peggy/Desktop/information retrieval/prj/test-collection/cacm"
    ListPath = "/Users/peggy/Desktop/information retrieval/prj/test-collection/cacm.rel.txt"
    QueryPath = "/Users/peggy/Desktop/information retrieval/prj/test-collection/cacm.query.txt"
    Stemfilepath = "/Users/peggy/Desktop/information retrieval/prj/test-collection/cacm_stem.txt"
    lucene_result_path = "/Users/peggy/Desktop/information retrieval/prj/task1/LUCENE_.txt"
    averageprepath = "/Users/peggy/Desktop/information retrieval/prj/average_precision.txt"


    # plot_recall_precision(averageprepath)

    lucenelist = []
    # lucenelist = pre.get_lucene_result(lucene_result_path)
    Que_dic = {}
    Doc_dic = {}
    Inv_list = {}
    Rel_dic = {}
    tfidf_weight_dict = {}

    # pre.create_query_list(QueryPath, Que_dic)
    pre.create_rel_list(ListPath, Rel_dic)
    # pre.creat_doc_list(FilePath, Doc_dic)


    pre.create_stem_doc_list(Stemfilepath, Doc_dic)
    # pre.parser(Doc_dic)
    inverted_list(Doc_dic, Inv_list)
    cal_tfidf_weight(Doc_dic, Inv_list, tfidf_weight_dict)

    Que_dic = {1: ["portabl", "oper", "system"],
               2:["code", "optim", "for", "space", "effici"],
               3:["distribut", "comput", "structur", "and", "algorithm"],
               4:["parallel", "algorithm "],
               5:["appli", "stochast", "process"],
                6:["perform", "evalu", "and", "model", "of", "comput", "system"],
                7:["parallel", "processor", "in", "inform", "retriev"]}

    stoplist = pre.create_stopword_list("/Users/peggy/Desktop/information retrieval/prj/stopwordlist.txt")

    method_evaluation(Que_dic, Doc_dic, Inv_list, Rel_dic, stoplist, lucenelist)


















