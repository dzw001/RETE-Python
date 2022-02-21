from common import *


class VarConsistencyTestNode:

    def __init__(self, var, pos, alpha_memory=None, children=None):
        self.var = var
        self.pos = pos
        self.alpha_memory = alpha_memory
        self.children = children if children else []
        self.field_to_test = pos
        self.symbol = var

    def __repr__(self):
        return "<VarConsistencyTestNode %s at %s?>" % (self.var, self.pos)

    def dump(self):
        return "%s at %s?" % (self.var, self.pos)

    def test(self, wme):
        to_compare = []
        for t in self.pos:
            to_compare.append(wme.content[t])

        return len(set(to_compare)) <= 1

    @staticmethod
    def build_or_share(parent, var, pos):

        for child in parent.children:
            if type(child) is VarConsistencyTestNode:
                if child.var == var and child.pos == pos:
                    return child

        new_node = VarConsistencyTestNode(var, pos)
        parent.children.append(new_node)
        return new_node

    def activation(self, wme):

        if not self.test(wme):
            return False

        if self.alpha_memory:
            self.alpha_memory.activate(wme)
        for child in self.children:
            child.activate(wme)


class ConstantTestNode:
    def __init__(self, field_to_test, field_must_equal=None, alpha_memory=None, children=None, variables=None):
        assert field_to_test in ['identifier', 'attribute', 'value', 'no-test']
        self.field_to_test = field_to_test  # 所检查的域
        self.field_must_equal = field_must_equal  # 测试的真值
        self.alpha_memory = alpha_memory  # 对应的 alpha memory ，若没有，则设为 None
        self.children = children if children else []  # 由 ConstantTestNode 对象组成的列表
        self.variables = variables if variables else {}

    def __repr__(self):
        return "<ConstantTestNode %s=%s?>" % (self.field_to_test, self.field_must_equal)

    def dump(self):
        return "%s=%s?" % (self.field_to_test, self.field_must_equal)

    def _constant_check(self, wme):
        return wme.content[self.field_to_test] == self.field_must_equal

    def _variables_check(self, wme):

        to_compare = []

        for var_name, fields in self.variables.items():
            if len(fields) > 1:
                to_compare = []
                for t in fields:
                    to_compare.append(wme.content[t])

        return len(set(to_compare)) <= 1
    
    def activate(self, wme: WME):
        if self.field_to_test != 'no-test':
            if not (self._constant_check(wme) and self._variables_check(wme)):
                return False
        if self.alpha_memory:
            self.alpha_memory.activate(wme)
        for child in self.children:
            child.activate(wme)

    @classmethod
    def build_or_share_alpha_memory(cls, node, constants=None, variables=None):
        if not constants:
            constants = []
        # constants 为空，说明当前已经没有需要测试的常数，即当前节点即是当前新增『条件』的最后一个 ConstantTestNode ，它应当连接一个 AlphaMemoryNode
        if not len(constants):
            # 如果当前 ConstantTestNode 已经有 alpha memory 节点，则返回，若没有，则创建并返回
            if not node.alpha_memory:
                node.alpha_memory = AlphaMemoryNode()
            return node.alpha_memory

        f, s = constants.pop(0)
        assert f in FIELDS, "`%s` not in %s" % (f, FIELDS)
        next_node = cls.build_or_share_constant_test_node(node, f, s, variables)

        # 递归地创建后续的 ContantTestNode，直到 AlphaMemoryNode 被成功创建为止
        return cls.build_or_share_alpha_memory(next_node, constants)

    @staticmethod
    def build_or_share_constant_test_node(parent, field, symbol, variables):
        for child in parent.children:
            if child.field_to_test == field and child.field_must_equal == symbol:
                return child
        new_node = ConstantTestNode(field, symbol, children=None, variables=variables)
        parent.children.append(new_node)
        return new_node


class AlphaMemoryNode:

    def __init__(self, items=None, children=None):
        self.items = items if items else []
        self.children = children if children else []

    def activate(self, wme: WME):
        if wme in self.items:
            return
        self.items.append(wme)
        wme.alpha_memories.append(self)
        # 之所以用 reversed(self.children) ，是为了避免 BetaMemoryNode 中存储重复的 token，具体见论文
        for child in reversed(self.children):
            child.right_activate(wme)
