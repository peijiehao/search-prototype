import preparation as pre
import math


def create_pos_invered_list(docdic, inv_list):
    for doc in docdic:
        for token in docdic[doc]:
            if token in inv_list and doc == inv_list[token][len(inv_list[token]) - 1][0]:
                continue
            count = 0
            poslist = []
            pos = 0
            for item in docdic[doc]:
                pos += 1
                if item == token:
                    count += 1
                    poslist.append(pos)
            list = [doc, count, poslist]
            if token not in inv_list:
                inv_list[token] = []
            inv_list[token].append(list)
    print "finish inverted list"



def BM25(inv_list, docdic, query):
    print "calculating BM25 document rank"
    k1 = 1.2
    b = 0.75
    ranklist = []
    N = float(len(docdic))
    length = 0
    for doc in docdic:
        length += len(docdic[doc])
    avdl = float(length / N)
    for doc in docdic:
        K = float(k1 * (float(1 - b) + b * float(len(docdic[doc])) / avdl))
        docrank = 0
        for term in query:
            if term in inv_list:
                ni = float(len(inv_list[term]))
                fi = 0.0
                for name in inv_list[term]:
                    if name[0] == doc:
                        fi = float(name[1])
            else:
                ni = 0.0
                fi = 0.0
            temp2 = (N - ni + 0.5) / (ni + 0.5)
            temp3 = (k1 + 1.0) * fi / (K + fi)
            docrank += math.log(temp2) * temp3
        ranklist.append([doc, docrank])
    ranklist.sort(key=lambda item: item[1], reverse=True)
    return ranklist


def find_in_N(content, i, target, N):
    '''
    check if target is within the window N from position i in content
    '''
    res = 0 # mark find target or not
    dis = 0 # distance of target from position i
    while i < len(content) and dis < N:
        if content[i] == target:
            res = 1
            break
        i += 1
        dis += 1
    return res, dis


def advanced_search():
    query_str = raw_input("input your query: " + '\n')
    # query_str =  "What articles exist which deal with TSS (Time Sharing System), an operating system for IBM computers?"
    query = pre.queryparser(query_str)
    select = raw_input("input your search criteria: exact/ best/ ordered best: " + '\n')
    # select = "ordered best"
    file_path = raw_input("input your document folder path:" + '\n')
    # file_path = "/Users/peggy/Desktop/information retrieval/prj/test-collection/cacm"
    Doc_dic = {}
    Inv_list = {}

    pre.creat_doc_list(file_path, Doc_dic)
    pre.parser(Doc_dic)

    create_pos_invered_list(Doc_dic, Inv_list)
    Rank_list = BM25(Inv_list, Doc_dic, query)

    Result_list = []

    if select == "exact":
        print "calculating exact match"
        for item in Rank_list:
            doc = item[0]
            flag = 0 # mark if this doc can be shown or not
            content = Doc_dic[doc]
            for i in range(len(content)):
                if content[i] == query[0]:
                    for j in range(len(query)):
                        if content[i + j] != query[j]:
                            break
                        if j == len(query) - 1:
                            flag = 1 # if all the query terms exist, doc can be shown
            if flag == 1 and len(Result_list) <= 100:
                Result_list.append(item)


    if select == "best":
        print "calculating best match"
        highest_rank = Rank_list[0][1]
        for item in Rank_list:
            doc = item[0]
            flag = 0 # mark if the document could be shown or not
            content = Doc_dic[doc]
            i = 0
            ad_score = 0 # extra score indicate the level of query match
            while i < len(content):
                for j in range(len(query)):
                    if content[i] == query[j]:
                        temp = i
                        flag = 1 # contains at least one query term
                        count = 0 # store the length of sub query
                        # find how long the match is
                        while temp < len(content) and j < len(query) and content[temp] == query[j]:
                            count += 1
                            temp += 1
                            j += 1
                        ad_score = max(ad_score, count) # the maximum length of sub query in this document
                        if temp != i:
                            i = temp - 1
                        break
                i += 1
            if flag == 1 and len(Result_list) <= 100:
                ad_score = (float(ad_score) / float(len(query))) * highest_rank # calculate the addition score
                # print item[0]
                # print ad_score
                Result_list.append([item[0], item[1] + ad_score])


    if select == "ordered best":
        N = int(raw_input("input your window size" + '\n'))
        print "calculating ordered best match"
        highest_rank = Rank_list[0][1]
        for item in Rank_list:
            doc = item[0]
            flag = 0
            content = Doc_dic[doc]
            i = 0
            ad_score = 0
            while i < len(content):
                for j in range(len(query)):
                    if content[i] == query[j]:
                        temp = i
                        flag = 1
                        count = 0
                        while j < len(query):
                            res, dis = find_in_N(content, temp, query[j], N)
                            if res == 0:
                                break
                            count += 1
                            j += 1
                            temp += dis + 1
                        # addition score is (max length of sub query / distance from the first term of sub query to the last)
                        ad_score = max(ad_score, float(count) / float(temp - i))
                        i = temp
                        break
                i += 1
            if flag == 1 and len(Result_list) <= 100:
                ad_score = (float(ad_score) / float(len(query))) * highest_rank
                # print item[0]
                # print ad_score
                Result_list.append([item[0], item[1] + ad_score])

    Result_list.sort(key=lambda item: item[1], reverse=True)
    print '\n'
    print "here are the results:"
    for item in Result_list:
        print item


if __name__ == '__main__':
    advanced_search()

