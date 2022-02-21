from rete import Rete
from common import Condition, WME


def test():
    rule_1 = [Condition('$x', 'on', '$y'), Condition('$y', 'left-of', '$z'), Condition('$z', 'color', 'red')]
    rule_2 = [Condition('$a', 'self', '$b'), Condition('$a', 'color', 'green')]
    wme_1 = WME('A', 'on', 'B')
    wme_2 = WME('B', 'left-of', 'C')
    wme_3 = WME('C', 'color', 'red')
    wme_4 = WME('B', 'color', 'green')
    wme_5 = WME('B', 'self', 'B')
    net = Rete()
    net.add_production(rule_1)
    print(net.dump())
    net.add_production(rule_2)
    print(net.dump())
    print('first add:')
    net.add_wme(wme_1)
    net.add_wme(wme_2)
    net.add_wme(wme_3)
    net.add_wme(wme_4)
    print('second add:')
    net.add_wme(wme_5)


if __name__ == '__main__':
    test()
    