# coding=utf-8
import json
import random

from .rulebase import RuleBase,Rule

###############################
#                             #
#  This class has deprecated  #
#                             #
###############################

class CustomRuleBase(RuleBase):

    """
    用于客制化比对的规则库，每次比对完即清空规则
    """

    #TODO 客制化的“阶段式对话”

    def customMatch(self, sentence, api_key, threshold):

        """
        比对 sentence 与用户自定义的规则

        Args:
            - sentence : 用户输入
            - api_key   : 该名会员的聊天机器人金钥

        Return: response, 暂时目标 FIXME
            - response : 批配出最适合的主题后，挑选用户于该主题定义的句子随机挑一回复
        """
        # 清空之前读入的规则
        self.rules.clear()

        # 重新建构规则表
        custom_rules = self.getCustomDomainRules(api_key)
        custom_rules = json.loads(custom_rules)
        self.buildCustomRules(custom_rules)

        # 进行比对
        result_list,path = self.match(sentence, threshold=0.4, root=api_key)

        # 确认最佳回应的有效性
        if result_list[0][0] < threshold:
            return None
            
        # 取出最佳主题的自订回复集, 并随机挑一句回复
        best_domain = result_list[0][1]
        target_rule = self.rules[best_domain]
        res_num = target_rule.has_response()

        return target_rule.response[random.randrange(0,res_num)]

    def buildCustomRules(self, rules):

        """
        将读入的规则从字典转换为 Rule Class 型式

        Args:
            - rules: 由 json.loads 导出的字典型式的规则
        """
        assert self.model is not None, "Please load the model before loading rules."

        for rule in rules:

            domain = rule["domain"]
            concepts_list = rule["concepts"]
            children_list = rule["children"]
            response = rule["response"]

            if domain not in self.rules:
                rule = Rule(domain, concepts_list, children_list, response, self.model)
                self.rules[domain] = rule
            else:
                #TODO Block invalided rule type on front end.
                print("[Rules]: Detect a duplicate domain name '%s'." % domain)

    def getCustomDomainRules(self, key):
        """
        依照 apiKey 取得该用户的规则集
        """
        #TODO
        #FIXME 采用正规方式验证

        data = '[{"domain": "TESTING","response": ["这是个测试客制化规则的回复1","这是个测试客制化规则的回复2"],"concepts": ["测试"],"children": []}]'

        return data
