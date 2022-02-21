from common import *
from alpha_net import AlphaMemoryNode

from typing import List


class BetaMemoryNode:
    
    def __init__(self, children=None, parent=None, items=None):
        self.children = children if children else []
        self.parent = parent
        self.items = items if items else []  # 存储 Token 对象的列表

    def dump(self):
        return "%s %s" % (self.__class__.__name__, id(self))

    def left_activate(self, token, wme):
        new_token = Token(token, wme, node=self)
        self.items.append(new_token)
        for child in self.children:
            child.left_activate(new_token)


class ProductionNode:
    '''
    p-node 的实现方式要根据具体的任务而定, 这里只给出一个简单的实现: 打印出满足当前 p-node 所对应规则的哪些 wme 的内容。 
    '''
    def __init__(self, parent=None, items=None, children=None, **kwargs):
        self.parent = parent
        self.items = items if items else []  # Token 对象组成的列表
        self.children = children if children else []
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def dump(self):
        return "%s %s" % (self.__class__.__name__, id(self))

    def left_activate(self, token, wme):
        new_token = Token(token, wme, node=self)
        self.items.append(new_token)
        print('a rule is satisfied with:')
        print(new_token.dump() + '\n')

    def execute(self, *args, **kwargs):
        raise NotImplementedError


class JoinNode:

    def __init__(self, children: List[BetaMemoryNode], parent: BetaMemoryNode, alpha_memory: AlphaMemoryNode, tests, condition):
        self.children = children
        self.parent = parent
        self.alpha_memory = alpha_memory
        self.tests = tests  # TestAtJoinNode 组成的列表
        self.condition = condition

    def dump(self):
        return "%s %s" % (self.__class__.__name__, id(self))

    def left_activate(self, token: Token):
        '''
        由 BetaMemoryNode 激活, 对 BetaMemoryNode 传过来的 token 
        进行 join test: 将该 token 与此 JoinNode 所对应的 AlphaMemoryNode
        中存储的所有 wme 分别执行 perform_join_test()。如果能通过测试, 则激活此
        JoinNode 的所有 children, 将通过测试的 『(token, wme)对』分别传递给它们。
        '''
        for wme in self.alpha_memory.items:
            if self.perform_join_test(token, wme):
                for child in self.children:
                    child.left_activate(token, wme)
    
    def right_activate(self, wme):
        '''
        由 AlphaMemoryNode 激活, 类似于上述的 left_activate。
        '''
        if not self.tests:
            for child in self.children:
                child.left_activate(None, wme)
        else:
            for token in self.parent.items:
                if self.perform_join_test(token, wme):
                    for child in self.children:
                        child.left_activate(token, wme)

    def perform_join_test(self, token: Token, wme: WME):
        '''
        检测『 wme 的 field_of_arg1 域上的值』与『 token 中存储的第
        condition_number_of_arg2 个 wme 的 field_of_arg2 域上的值』
        是否相等。
        '''
        for test in self.tests:
            arg1 = wme.content[test.field_of_arg1]
            wme2 = token.wmes[test.condition_number_of_arg2]
            arg2 = wme2.content[test.field_of_arg2]
            if arg1 != arg2:
                return False
        return True

class TestAtJoinNode:

    def __init__(self, field_of_arg1, condition_number_of_arg2, field_of_arg2):
        self.field_of_arg1 = field_of_arg1
        self.condition_number_of_arg2 = condition_number_of_arg2
        self.field_of_arg2 = field_of_arg2

    def __eq__(self, other):
        return isinstance(other, TestAtJoinNode) and \
            self.field_of_arg1 == other.field_of_arg1 and \
            self.field_of_arg2 == other.field_of_arg2 and \
            self.condition_number_of_arg2 == other.condition_number_of_arg2
