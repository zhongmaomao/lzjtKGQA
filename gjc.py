from ltp import LTP
from py2neo import Graph
import re
import os


graphIP = "bolt://neoforj.zhinengwenda-test.svc.cluster.hz:30665"
username = "neo4j"
password = "mercy-france-collect-gong-window-7317"


# env_list = os.environ
# graphIP = env_list['graph']
# username = env_list['username']
# password = env_list['password']



# 解析器，用于解析问题中的意图
# 返回包含主题词，问题词，问题焦点等在内的问题意图
class Resolver:
    def __init__(self):
        self.ltp = LTP()

    # 解析问题
    def resolve_question(self, text):
        # 先交给ltp模型处理，主要获得分词的词性和语法依存关系
        # output = self.ltp.pipeline([text], tasks=["cws", "pos", "ner", "srl", "dep", "sdp"])
        output = self.ltp.pipeline([text], tasks=["cws"])
        seg = output.cws[0]
        # pos = output.pos[0]
        # srl = output.srl
        # sdp = output.sdp


        # 依据词性，找到问题的动词和主题词
        # qverb = None
        # for i in range(len(seg)):
        #     p = pos[i]
        #     if p is "v":
        #         qverb = seg[i]
        #         break

        # 根据预定义的关键词，找到问题的问题词是什么以及位置
        # keywords = ["路线", "什么", "谁"]
        # qwords = []
        # for i in range(len(seg)):
        #     word = seg[i]
        #     for key in keywords:
        #         if word.__contains__(key):
        #             qwords.append((word, i))
        #
        # # 依据语义角色关系，确定问题的主题词
        # qtopics = []
        # for line in srl:
        #     if len(line) != 0:
        #         for role in line:
        #             role_name = role['predicate']
        #             role_content = role['arguments'][0][1] + role['arguments'][1][1]
        #             test = True
        #             for key in keywords:
        #                 test = True
        #                 if role_content.__contains__(key):
        #                     test = False
        #                     break
        #             if test:
        #                 qtopics.append((role_content, role_name))

        # 确定问题的问题焦点

        return {"intent": "find_roadnum", "seg": seg}


class QABot:
    def __init__(self):
        # self.classifier = SiwiClassifier()
        # self.actions = SiwiActions()
        # self.connection_pool = connection_pool
        self.resolver = Resolver()
        self.graph = Graph(graphIP, auth=(username, password))

    def query(self, sentence):
        res = self.resolver.resolve_question(sentence)
        intent = res['intent']
        seg = res['seg']
        num = ""
        for word in seg:
            if(word[0] == '桂'):
                num = word
        if num == "":
            return "no record"
        qrl = 'match (person:人员) -[r:驾驶]->(vehical:车辆) where vehical.name = "' + num + '" return person.name'
        result = self.graph.run(qrl)
        answer = ""
        for record in result:
            if answer != "":
                answer += ','
            answer += record[0]

        # intent = self.classifier.get(sentence)  # <--- a.
        # action = self.actions.get(intent)       # <--- b.
        if answer == "":
            return "no record"
        else:
            return "驾驶过车辆" + num + "的司机有:" + answer  #action.execute(self.connection_pool)

# class find_roadnum:
#     def __init__(self):



if __name__ == "__main__":
    qrl = 'match (person:人员) -[r:驾驶]->(vehical:车辆) where vehical.name = "桂B11555" return person.name'
    graph = Graph(graphIP, auth=(username, password))
    result = graph.run(qrl)
    answer = ""
    for record in result:
        if answer != "":
            answer += ','
        answer += record[0]

    print(answer)


