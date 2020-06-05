# -*- encoding: utf-8 -*-
"""
@Author: Gavin
@File: reimplement_keywordtree.py
@Time:2020/6/3
@Software: Pycharm
@Desc: 手动实现AC自动机
"""

from copy import deepcopy


class State(object):
    """一个State实例就是一个节点，需要包含属性:
        symbol: 节点链上的字符
        state_id: 状态序号
        transitions: 节点的子节点
        parent: 节点的父节点
        keyword: 该节点是关键词的最后一个字符
        failure: 节点failure路径指向的节点
        success: 所有的词是否全部添加进入字典树
    """
    def __init__(self, state_id, symbol=None, parent=None, success=False):
        self.state_id = state_id
        self.symbol = symbol
        self.parent = parent
        self.success = success
        self.transitions = {}
        self.keyword = None
        self.failure = None

    def __str__(self):
        transitions_as_string = ','.join(
            ['{0} -> {1}'.format(key, value.state_id) for key, value in self.transitions.items()])
        return "State {0}. Transitions: {1}".format(self.state_id, transitions_as_string)


class KdTree(object):
    """AC字典树

    """
    def __init__(self, case_sensitive=True):
        self._zero_node = State(0)
        self.case_sensitive = case_sensitive
        self._counter = 1
        self._finalized = False

    def add_keyword(self, keyword):
        """添加关键词
        :param keyword:
        :return:
        """
        if self._finalized:
            raise ValueError("字典树已经构建完成，不能再添加新词")
        origin_keyword = deepcopy(keyword)
        if not self.case_sensitive:
            keyword = keyword.lower()
        current_node = self._zero_node
        for character in keyword:
            if character not in current_node.transitions:
                next_node = State(self._counter, parent=current_node, symbol=character)
                self._counter += 1 # 表示状态序号
                current_node.transitions[character] = next_node
                current_node = next_node
            else:
                current_node = current_node.transitions[character]
        current_node.success = True
        current_node.keyword = origin_keyword

    def finalize(self):
        if self._finalized:
            raise ValueError("字典树已经构建完成，不能再添加failure路径")
        self._zero_node.failure = self._zero_node # 因为不会对根节点的failure进行判断，所以事先指定
        self.find_failure_for_children(self._zero_node)
        self._finalized = True # 当所有的节点都操作完毕后，finalized设置为True，表示failure全部添加完，字典树构建完毕

    def find_failure_for_children(self, zero_node):
        to_add_failure_nodes = [zero_node]  # 要进行failure添加的节点
        processed_node_id = set()  # 已经添加过的节点的state_id
        while to_add_failure_nodes:
            current_node = to_add_failure_nodes.pop()
            if current_node.state_id not in processed_node_id:
                processed_node_id.add(current_node.state_id)
                children = current_node.transitions.values()
                for child in children:
                    self.find_failure(child)  # 为子节点找到failure指针指向的节点
                    to_add_failure_nodes.append(child)

    def find_failure(self, node):
        """找到节点的failure路径

        :param child:
        :return:
        """
        if node.failure is None:
            traversed_node = node.parent.failure
            while True:
                if node.symbol in traversed_node.transitions and node != traversed_node.transitions[node.symbol]:
                    node.failure = traversed_node.transitions[node.symbol]
                    for symbol, node in node.failure.transitions.items():
                        if symbol not in node.transitions:
                            node.transitions[symbol] = node
                    break
                elif traversed_node == self._zero_node:
                    node.failure = self._zero_node
                    break
                else:
                    traversed_node = traversed_node.failure

    def search_all(self, text):
        """搜索关键词"""
        if not self._finalized:
            raise ValueError("字典树尚未构建完成，需要先构建好字典树才能进行关键词搜索")
        if not self.case_sensitive:
            text = text.lower()
        current_node = self._zero_node
        for idx, symbol in enumerate(text):
            if symbol in current_node.transitions:
                if current_node.transitions[symbol].success:
                    keyword = current_node.transitions[symbol].keyword
                    yield (keyword, idx+1-len(keyword))
                else:
                    current_node = current_node.transitions[symbol]
            else:
                continue


if __name__ == "__main__":
    kdtree = KdTree(case_sensitive=False)
    for i in ["中华人民共和国", "美利坚合众国", "国中", "樱木花道", "赤木晴子", "流川枫", "赤木刚宪"]:
        kdtree.add_keyword(i)
    kdtree.finalize()
    sentence = "中华人民共和国简称中国， 最近和美利坚进行贸易战，但是我不care， 我闲暇时候看了看灌南高手，里面的樱木喜欢晴子，晴子仰慕流川枫， 赤木刚宪哈皮"
    results = kdtree.search_all(sentence)
    for result in results:
        print(result)
