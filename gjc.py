from ltp import LTP
from py2neo import Graph
import re
import os


graphIP = "neo4j://neoforj.zhinengwenda-test.svc.cluster.hz:31700"
username = "neo4j"
password = "crash-diploma-nuclear-spiral-common-5580"


env_list = os.environ
graphIP = env_list['graph']
username = env_list['username']
password = env_list['password']



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


# TODO 目前仍存在一下几个问题
# 1.对时间和地点人物的处理基本可用，涉及组织的答案还有待测试
# 2.在组织查询的时候对没有组织，人名，地点等不存在的情况做出考虑（查询会出错）
# 重点修改对查询语句的组织
class Selector:

    def __init__(self, graph):
        self.graph = graph

    def get_answer(self, q_result):
        time_pattern = "((\d+)年)?((\d+)月)?((\d+)(日|号))?"
        event_cql = "match (e:事件) where true "
        event_attr_select_tmp = " and e.description =~ '.*{qtopic}.*' "
        time_cql = "match p2 = (e)-[]-(d:`日`)-[]-(m:`月`)-[]-(y:`年`) where true "
        loc_cql = "match p1 = (e) -[]-(l:`地点`) "
        people_cql = "match p3 = (e)-[]-(p:`人物`) "
        # 第一步应该先根据主题词来确定问题涉及的知识图中的具体实体
        for qtopic in q_result["qtopics"]:
            if qtopic[1].__contains__("TMP"):
                time_result = re.match(time_pattern, qtopic[0])
                year = time_result.group(2)
                month = time_result.group(4)
                day = time_result.group(6)
                if year is not None:
                    time_cql += " and y.name = '{}' ".format(year)
                if month is not None:
                    time_cql += " and m.name = '{}' ".format(month)
                if day is not None:
                    time_cql += " and d.name = '{}' ".format(day)
            elif qtopic[1].__contains__("LOC"):
                pass
            else:
                event_cql += event_attr_select_tmp.format(qtopic=qtopic[0])

        # 第二步，根据问题词和问题焦点确定答案的类型
        return_tmp = "return e"
        answer_type = None
        time_keywords = ["时候", "时间", "年", "月", "日"]
        place_keywords = ["省", "市", "区", "州", "哪里"]
        people_keywords = ["谁"]
        org_keywords = ["组织", "协会", "会", "集团", "部", "大学", "局", "组", "院", "公司", "行"]
        for qf in q_result["qfocus"]:
            if qf in time_keywords:
                answer_type = "时间"
            elif qf in place_keywords:
                answer_type = "地点"
            elif qf in people_keywords:
                answer_type = "人物"
            elif qf in org_keywords:
                answer_type = "组织"
        for qrel in q_result["qrels"]:
            if qrel is "TIME":
                answer_type = "时间"
            elif qrel is "LOC":
                answer_type = "地点"
            elif answer_type is None:
                answer_type = "事件"
        if answer_type is "时间":
            return_tmp += ",y,m,d"
        elif answer_type is "地点":
            event_cql += "\n" + loc_cql
            return_tmp += ",l"
        elif answer_type is "人物":
            event_cql += "\n" + people_cql
            return_tmp += ",p"

        # 依据qrel来作为辅助信息，完善查询
        cql = event_cql + "\n" + time_cql + "\n" + return_tmp
        return cql

    def regular_answer(self, question, cql):
        result = self.graph.run(cql).to_subgraph()
        if result is None:
            print("没找到相关问题的答案")
        else:
            nodes = result.nodes
            for node in nodes:
                if "事件" in node.labels:
                    print(node["description"])
                else:
                    if not question.__contains__(node["name"]):
                        for label in node.labels:
                            print(label, end=":")
                        print(node["name"])

    # Success
    # interval中传一个时间范围,范例如下
    # {start_year:2017,start_month:1,start_day:1,end_year:2017,end_month:1,end_day:10}表示在2017.1.1到2017.1.10的时间范围
    def condition_select(self, interval=None, fields=None, place=None):
        # 1找到时间范围内的事件节点
        select_cql = ""
        time_cql = "match (y:`年`)<-[:`时间属于`]-(m:`月`)<-[:`时间属于`]-(d:`日`)-[:`开始时间`]-(e:`事件`) "
        if interval is not None:
            time_select_cql = "where ((y.value > {start_year} and y.value < {end_year}) " \
                       "or ({start_year} = {end_year} and {start_month} = {end_month} and y.value = {start_year} and m.value = {start_month} and d.value >= {start_day} and d.value <= {end_day}) " \
                       "or ({start_year} = {end_year} and {start_month} < {end_month} and y.value = {start_year} and ((m.value = {start_month} and d.value >= {start_day}) or (m.value > {start_month} and m.value < {end_month}) or (m.value = {end_month} and d.value <= {end_day}))) " \
                       "or ({start_year} < {end_year} and y.value = {start_year} and ((m.value > {start_month}) or (m.value = {start_month} and d.value >= {start_day}))) " \
                       "or ({start_year} < {end_year} and y.value = {end_year} and ((m.value < {end_month}) or (m.value = {end_month} and d.value <= {end_day}))))"
            time_select_cql = time_select_cql.format(**interval)
            time_cql += time_select_cql
        select_cql += time_cql + "\n"
        # 2找到所属领域内的事件节点
        field_cql = "match (e:`事件`)-[:`所属领域`]-(f:`领域`) "
        if fields is not None:
            field_select_cql = "where f.field in " + fields.__str__()
            if len(fields) != 0:
                field_cql = field_cql + field_select_cql
        select_cql += field_cql + "\n"
        # 3找到地理位置下的所有事件节点
        place_cql = "match (l:`地点`) "
        place_path_cql = "match p = (e:`事件`)-[r:`事件地点`]->(:`地点`)-[:`地点属于` * 0..4]->(l)"
        if place is not None:
            place_cql += "where l.name = '{}'".format(place)
            place_cql += "\n" + place_path_cql
            select_cql += place_cql
        select_cql += "\n" + "return distinct id(e),date(y.name + '-'+m.name+'-'+d.name) as time ,e.description order by time"

        # 4交给graph去查找，组织答案
        result = self.graph.run(select_cql).to_data_frame()["e.description"].to_list()
        return result

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


