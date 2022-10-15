# -*- coding: utf-8 -*-
import os
import random

import console
import task_modules.module_switch as module_switch
import RuleMatcher.customRuleBase as crb
import QuestionAnswering.KB_QA as qa

class Chatbot(object):

    def __init__(self, name="聊天机器人", build_console=True, w2v_model_path="model/word2vec_model.model"):

        """
        # Args:
         - build_console: 是否要建构依照词向量进行主题匹配的 console,
         如果只需要 qa 模组，可将 build_console 关闭，可见 demo_qa.py
        """

        self.name = name             # The name of chatbot.

        self.speech = ''             # The lastest user's input
        self.speech_domain = ''      # The domain of speech.
        self.speech_matchee = ''     # The matchee term of speech.
        self.speech_path = None      # The classification tree traveling path of speech.
        self.speech_seg = []

        self.root_domain = None      # The root domain of user's input.
        self.domain_similarity = 0.0 # The similarity between domain and speech.

        cur_dir = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        self.extract_attr_log = open('log/extract_arrt.log','w',encoding='utf-8')
        self.exception_log = open('log/exception.log','w',encoding='utf-8')
        os.chdir(cur_dir)

        # For rule matching
        if build_console:
            self.console = console.Console(model_path=w2v_model_path)
            # self.custom_rulebase = crb.CustomRuleBase() # for one time matching.
            # self.custom_rulebase.model = self.console.rb.model # pass word2vec model

        # For Question Answering
        self.github_qa_unupdated = False
        if not self.github_qa_unupdated:

            try:
                self.answerer = qa.Answerer()
            except Exception as exc:
                print("[QA] 请确认问答资料集的目录结构是否正确")
                print("[QA] ")

        self.default_response = [
            "是吗?",
            "我不太明白你的意思",
            "原来如此"
        ]

    def waiting_loop(self):

        print("你好，我是 " + self.name)
        while True:

            speech = input()
            res = self.listen(speech)
            print(res[0])

    def listen(self, sentence, target=None, api_key=None, qa_threshold=35, qa_block_threshold=60):

        """
        listen function is to encapsulate the following getResponse methods:

            1.getResponseOnRootDomains(sentence,target)
            2.getResponseForGeneralQA(sentence)

        1 is to measure the consine similarity between keywords and sentence.
        2 is to measure the levenshtein distance between sentence and the questions
        in database/corpus.

        Args:
            - target : Optional. It is to define the user's input is in form of
            a sentence or a given answer by pressing the bubble buttom.
            If it is come from a button's text, target is the attribute name our
            module want to confirm.
            - api_key : for recognizing the user and get his custom rule/QAs.

        Return: [response,status,target,candiates]
            - response : Based on the result of modules or a default answer.
            - status   : It would be the module's current status if the user has
                         been sent into any module and had not left it.
            - target   : Refer to get_query() in task_modules/task.py
            - candiates: Refer to get_query() in task_modules/task.py
        """
        response = None
        stauts = None
        target = None
        candiates = None

        # First of all,
        # Assume this sentence is for qa, but use a very high threshold.
        qa_response, qa_sim = self.getResponseForQA(sentence,qa_threshold)
        if qa_sim > qa_block_threshold:
            return qa_response,None,None,None,None

        # do the rule matching.
        is_confident = self.rule_match(sentence, threshold=0.4)

        if is_confident:
            response,stauts,target,candiates = self.getResponseOnRootDomains(target)
            return response,stauts,target,candiates

        # The result based on custom rules and general rules are not confident.
        # Assume that there are no intent in the sentence, consider this questions
        # is qa again, but this time use a smaller threshold.
        else:
            if qa_sim > qa_threshold:
                return qa_response,None,None,None
            else:
                # This query has too low similarity for all matching methods.
                # We can only send back a default response.
                return self.getDefaultResponse(),None,None,None

    def getResponseOnRootDomains(self, target=None):

        """
        Send back a response and some history information based on the former
        result that came from rule_match().

        Args:
            - target  : Optional. It is to define the user's input is in form of
            a sentence or a given answer by pressing the bubble buttom.
            If it is come from a button's text, target is the attribute name our
            module want to confirm.

        Return:
            - response : Based on the result of modules or a default answer.
            - status   : It would be the module's current status if the user has
                         been sent into any module and had not left it.
            - target   : Refer to get_query() in task_modules/task.py
            - candiates: Refer to get_query() in task_modules/task.py
        """

        status = None
        response = None

        handler = self._get_task_handler()

        try:
            status,response = handler.get_response(self.speech, self.speech_domain, target)
        except AttributeError:
            # It will happen when calling a module which have not implemented.
            # If you require more detailed information,
            # please refer module_switch.py and  task.py in the folder "task_modules".
            exception = "Handler of '%s' have not implemented" % self.root_domain
            print(exception)
            self.exception_log.write(exception)
            return [self.getDomainResponse(),None,None,None]

        if response is None:
            response = self.getDomainResponse()

        if status is None:
            # One pass talking, this sentence does not belong to any task.
            return [response,None,None,None]
        else:
            target,candiates = handler.get_query()
            handler.debug(self.extract_attr_log)
            return [response,status,target,candiates]

    def getResponseForQA(self, sentence, threshold=0):
        """
        Encapsulate getResponseForGeneralQA
        For details on the matching method, please refer PTT-Chat-Generator repo on github.

        Return:
            - response, similarity
            if the similarity < threshold will return None,0.
        """

        #FIXME Remove this flag when all have done.
        if self.github_qa_unupdated:
            return None, 0

        response,sim = self.answerer.getResponse(sentence)

        if sim > threshold:
            return response,sim

        return None,0

    def rule_match(self, speech, threshold):

        """
        Set domain,path,similarity,root_domain based on the rule which has
        the best similarity with user's input.

        Return: a boolean value, to indicate that this match makes sense or not.
        """

        res,self.last_path = self.console.rule_match(speech, best_only=True)
        self.speech = speech
        self.domain_similarity,self.speech_domain,self.speech_matchee = res
        self._set_root_domain()

        if self.domain_similarity < threshold:
            return False
        else:
            return True

    def getDomainResponse(self, domain=None):

        """
        Generate a response to user's speech.
        Please note that this response is *pre-defined in the json file*,
        is not the result return by sub_module.
        """

        if domain is None:
            domain = self.speech_domain
        response = self.console.get_response(domain)
        return response

    def getDefaultResponse(self, query=None):

        """
        Send back a default response.
        """

        # TODO @zake7749: update the attn-seq2seq code to github.

        return self.default_response[random.randrange(0,len(self.default_response))]

    def testQuestionAnswering(self, sentence):

        """
        专用于 QA 回复，回传(最佳回应、信心度)
        """
        # 默认 QA 库，无阀值采用 BM25，关闭远端 API
        if self.github_qa_unupdated:
            return ("Can not find the PTT CORPUS.",0)

        qa_response, qa_confidence = self.getResponseForQA(sentence)
        return (qa_response, qa_confidence)

    def testDomainAnswering(self):

        """
        专用于 Domain 的阶层式匹配，回传(模组回应、匹配路径、信心度)
        """
        # 默认规则库，无阀值，关闭远端 API
        # @zake7749 没有实现的必要性

        pass

    def testSeq2Seq(self):

        # TODO
        pass

    def _set_root_domain(self):

        """
        Extract the root rule in result.
        """
        if self.last_path == "":
            self.root_domain = self.speech_domain
        else:
            self.root_domain = self.last_path.split('>')[0]

    def _get_task_handler(self, domain=None):

        """
        Get the instance of task handler based on the given domain.
        """

        if domain is None:
            domain = self.root_domain

        switch  = module_switch.Switch(self.console)
        handler = switch.get_handler(domain)

        return handler

    def getLoggerData(self):

        """
        Deprecated.
        """

        return [self.root_domain,
                self.speech_domain,
                console.jieba.cut(self.speech,cut_all=False)]
