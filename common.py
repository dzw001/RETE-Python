FIELDS = ['identifier', 'attribute', 'value']


class WME:

    def __init__(self, id, attr, value):
        self.content = {'identifier': id, 'attribute': attr, 'value': value}
        self.alpha_memories = []  # 存储所有包含了这个 wme 的 AM
        self.tokens = []  # 存储所有包含有这个 wme 的 token
    
    def __eq__(self, other):
        return isinstance(other, WME) and self.content == other.content

    def dump(self):
        return '(%s, %s, %s)' % (self.content['identifier'], self.content['attribute'], self.content['value'])


class Token:

    def __init__(self, parent, wme, node=None):
        self.children = []  # 当前 token 的孩子，是一个由 Token 组成的列表
        self.parent = parent  # 当前 token 的父母（也是一个 Token 对象）
        self.wme = wme
        self.node = node  # 指向当前 token 所在的 memory_node
        if self.wme:
            self.wme.tokens.append(self)
        if self.parent:
            self.parent.children.append(self)

    def __eq__(self, other):
        return isinstance(other, Token) and self.parent == other.parent and self.children == other.children

    def dump(self):
        dumps = [self.wme.dump()]
        token = self
        while not token.is_root():
            token = token.parent
            dumps.append(token.wme.dump())
        return '[' + ', '.join(dumps) + ']'

    def is_root(self):
        return self.parent is None

    @property
    def wmes(self):
        wmes = [self.wme]
        token = self
        while not token.is_root():
            token = token.parent
            wmes.append(token.wme)
        return wmes[::-1]
    
    @classmethod
    def delete_descendents_of_token(cls, t):
        while t.children != []:
            cls.delete_token_and_descendents(t.children[0])
    
    @classmethod
    def delete_token_and_descendents(cls, token):
        for child in token.children:
            cls.delete_token_and_descendents(child)
        token.node.items.remove(token)
        if token.wme:
            token.wme.tokens.remove(token)
        if token.parent:
            token.parent.children.remove(token)


class Condition:

    def __init__(self, identifier, attribute, value):
        self.identifier = identifier
        self.attribute = attribute
        self.value = value
    
    def __eq__(self, other):
        return isinstance(other, Condition) and \
            self.identifier == other.identifier and \
            self.attribute == other.attribute and \
            self.value == other.value
    
    @property
    def vars(self):
        ret = []
        for field in FIELDS:
            v = getattr(self, field)
            if is_var(v):
                ret.append((field, v))
        return ret

    def contain(self, v):
        for f in FIELDS:
            if getattr(self, f) == v:
                return f
        return ""

    def test(self, wme):
        for f in FIELDS:
            v = getattr(self, f)
            if is_var(v):
                continue
            if v != wme.content[f]:
                return False
        return True


def is_var(v):
    return v.startswith('$')