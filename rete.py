
from io import StringIO
from alpha_net import *
from beta_net import *
from common import *


class Rete:
    def __init__(self):
        self.alpha_root = ConstantTestNode('no-test', alpha_memory=AlphaMemoryNode())
        self.beta_root = BetaMemoryNode()

    def dump(self):
        self.buf = StringIO()
        self.buf.write('digraph {\n')
        self.dump_beta(self.beta_root)
        self.dump_alpha(self.alpha_root)
        self.dump_alpha2beta(self.alpha_root)
        self.buf.write('}')
        return self.buf.getvalue()

    def dump_alpha(self, node):
        if node == self.alpha_root:
            self.buf.write("    subgraph cluster_0 {\n")
            self.buf.write("    label = alpha\n")
        for child in node.children:
            self.buf.write('    "%s" -> "%s";\n' % (node.dump(), child.dump()))
            self.dump_alpha(child)
        if node == self.alpha_root:
            self.buf.write("    }\n")

    def dump_alpha2beta(self, node):
        if node.alpha_memory:
            for child in node.alpha_memory.children:
                self.buf.write('    "%s" -> "%s";\n' % (node.dump(), child.dump()))
        for child in node.children:
            self.dump_alpha2beta(child)

    def dump_beta(self, node):
        if node == self.beta_root:
            self.buf.write("    subgraph cluster_1 {\n")
            self.buf.write("    label = beta\n")
        for child in node.children:
            self.buf.write('    "%s" -> "%s";\n' % (node.dump(), child.dump()))
            self.dump_beta(child)
        if node == self.beta_root:
            self.buf.write("    }\n")

    def add_wme(self, wme: WME):
        self.alpha_root.activate(wme)

    def remove_wme(self, wme: WME):
        for am in wme.alpha_memories:
            am.items.remove(wme)
        for t in wme.tokens:
            Token.delete_token_and_descendents(t)

    def add_production(self, rule, **kwargs):
        assert len(rule) > 0, 'rule should not be empty.'
        current_node = self.beta_root
        earlier_conditions = []
        tests = self.get_join_tests_from_condition(rule[0], earlier_conditions)
        alpha_memory = self.build_or_share_alpha_memory(rule[0])
        current_node = self.build_or_share_join_node(current_node, alpha_memory, tests, rule[0])
        for i in range(1, len(rule)):
            current_node = self.build_or_share_beta_memory(current_node)
            earlier_conditions.append(rule[i - 1])
            tests = self.get_join_tests_from_condition(rule[i], earlier_conditions)
            alpha_memory = self.build_or_share_alpha_memory(rule[i])
            current_node = self.build_or_share_join_node(current_node, alpha_memory, tests, rule[i])
        p_node = self.build_or_share_p_node(current_node, **kwargs)
        self.update_new_node_with_matches_from_above(p_node)
        return p_node

    def remove_production(self, node: ProductionNode):
        self.delete_node_and_any_unused_ancestors(node)

    def build_or_share_beta_memory(self, parent):
        for child in parent.children:
            if isinstance(child, BetaMemoryNode):
                return child
        node = BetaMemoryNode(children=None, parent=parent, items=None)
        parent.children.append(node)
        self.update_new_node_with_matches_from_above(node)
        return node
    
    def get_join_tests_from_condition(self, c, earlier_conds):
        result = []
        for field_of_v, v in c.vars:
            for idx, cond in enumerate(earlier_conds):
                field_of_v2 = cond.contain(v)
                if not field_of_v2:
                    continue
                t = TestAtJoinNode(field_of_v, idx, field_of_v2)
                result.append(t)
        return result

    def build_or_share_alpha_memory(self, condition):
        constants = []
        variables = {}

        for f in FIELDS:
            v = getattr(condition, f)
            if not is_var(v):
                constants.append((f, v))
            else:
                variables.setdefault(v, []).append(f)

        if len(constants) == 0:
            node = self.build_or_share_var_consistency_test_node(self.alpha_root, variables)
        else:
            node = self.alpha_root

        alpha_memory = ConstantTestNode.build_or_share_alpha_memory(
            node,
            constants,
            variables
        )
        # 存疑，但此处暂时不用考虑
        for w in self.alpha_root.alpha_memory.items:
            if condition.test(w):
                alpha_memory.activate(w)
        return alpha_memory
    
    def build_or_share_join_node(self, parent, alpha_memory, tests, condition):
        for child in parent.children:
            if isinstance(child, JoinNode) and child.alpha_memory == alpha_memory \
                    and child.tests == tests and child.condition == condition:
                return child
        node = JoinNode([], parent, alpha_memory, tests, condition)
        parent.children.append(node)
        alpha_memory.children.append(node)
        return node

    def build_or_share_p_node(self, parent, **kwargs):
        for child in parent.children:
            if isinstance(child, ProductionNode):
                return child
        node = ProductionNode(parent, **kwargs)
        parent.children.append(node)
        self.update_new_node_with_matches_from_above(node)
        return node
    
    def update_new_node_with_matches_from_above(self, new_node):
        parent = new_node.parent
        if isinstance(parent, BetaMemoryNode):
            for tok in parent.items:
                new_node.left_activate(tok, None)
        elif isinstance(parent, JoinNode):
            saved_list_of_children = parent.children
            parent.children = [new_node]
            for item in parent.alpha_memory.items:
                parent.right_activate(item)
            parent.children = saved_list_of_children

    def build_or_share_var_consistency_test_node(node, variables):
        for var, fields in variables.items():
            if len(fields) > 1:
                node = VarConsistencyTestNode.build_or_share(node, var, fields)
        return node

    def delete_node_and_any_unused_ancestors(self, node):
        if isinstance(node, JoinNode):
            node.alpha_memory.children.remove(node)
            # 删除无用的 alpha memory 节点以及 const test 节点。待完善。
            # if not node.alpha_memory.children:
            #     cls.delete_alpha_memory_node(node.alpha_memory)
        else:
            for item in node.items:
                Token.delete_token_and_descendents(item)
        node.parent.children.remove(node)
        if not node.parent.children:
            self.delete_node_and_any_unused_ancestors(node.parent)
        