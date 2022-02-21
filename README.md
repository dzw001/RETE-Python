# RETE-Python
用 Python 实现的一个简易的 RETE 。

测试流程（可参考 ```test.py``` 中的内容编写任意的测试 demo）：

1. 使用 ```net = RETE()``` 初始化 RETE 网络
2. 用一个由 ```Condition``` 对象组成的列表来定义一条 **规则** ，并调用 ```net.add_production()``` 来添加规则
3. 用 ```WME``` 对象来定义一条描述当前系统状态的 **事实** ，并调用 ```net.add_wme()``` 来添加新的系统状态
4. 如果当前的系统状态满足了某条规则，则会打印出满足规则的 **事实** 的内容
5. 在每次加入规则后，RETE 网络的结构都会发生变化，可以通过 ```print(net.dump())``` 来查看当前网络中节点的链接情况


参考文献：[Production Matching for Large Learning Systems](http://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=27AD61CD1B6A00CCA3DD5B6F9BBD383E?doi=10.1.1.83.4551&rep=rep1&type=pdf)

文献阅读笔记及复现代码的结构整理：[RETE笔记](https://blog.csdn.net/FANFANHEBAOER/article/details/123048486)
