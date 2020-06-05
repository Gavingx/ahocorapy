'''
Ahocorasick implementation entirely written in python.
Supports unicode.

Quite optimized, the code may not be as beautiful as you like,
since inlining and so on was necessary

Created on Jan 5, 2016

@author: Frederik Petersen (fp@abusix.com)
'''

from builtins import object


"""
edit by gavin:
在代码中： 
State类可以理解为节点，每一个节点包含symbol(表示某一个字符), identifier(表示当前节点的状态序号),parent(表示父节点),
transitions(表示子节点), success(表示是否匹配到字符), matched_keyword(表示匹配到的关键词), longest_strict_suffix(指failure
指向的节点

KeywordTree就是字典树的类，zero_state表示根节点，_counter实际上也是表示当前节点的状态序号（会作为参数传给State类）
_finalized表示字典树是否构建完成，只有在构建完成后，才能进行字符串匹配，一旦构建完成后就不能再添加关键词，
_case_insensitive表示是否大小写敏感，True表示不敏感，False表示大小写敏感


当前节点的failure状态指向父节点failure下的其他节点（如果字符能匹配上）
如果不能匹配上，则去父节点failure指向节点的failure状态指向的节点中去寻找是否能匹配上
"""


class State(object):
    __slots__ = ['identifier', 'symbol', 'success', 'transitions', 'parent',
                 'matched_keyword', 'longest_strict_suffix']

    def __init__(self, identifier, symbol=None,  parent=None, success=False):
        self.symbol = symbol
        self.identifier = identifier
        self.transitions = {}
        self.parent = parent
        self.success = success
        self.matched_keyword = None
        self.longest_strict_suffix = None

    def __str__(self):
        transitions_as_string = ','.join(
            ['{0} -> {1}'.format(key, value.identifier) for key, value in self.transitions.items()])
        return "State {0}. Transitions: {1}".format(self.identifier, transitions_as_string)


class KeywordTree(object):

    def __init__(self, case_insensitive=False):
        '''
        @param case_insensitive: If true, case will be ignored when searching.
                                 Setting this to true will have a positive
                                 impact on performance.
                                 Defaults to false.
        @param over_allocation: Determines how big initial transition arrays
                                are and how much space is allocated in addition
                                to what is essential when array needs to be
                                resized. Default value 2 seemed to be sweet
                                spot for memory as well as cpu.
        '''
        self._zero_state = State(0)
        self._counter = 1
        self._finalized = False
        self._case_insensitive = case_insensitive

    def add(self, keyword):
        '''
        Add a keyword to the tree.
        Can only be used before finalize() has been called.
        Keyword should be str or unicode.
        '''
        if self._finalized:
            raise ValueError('KeywordTree has been finalized.' +
                             ' No more keyword additions allowed')
        original_keyword = keyword
        if self._case_insensitive:
            keyword = keyword.lower()
        if len(keyword) <= 0:
            return
        current_state = self._zero_state
        for char in keyword:
            try:
                current_state = current_state.transitions[char]
            except KeyError:
                next_state = State(self._counter, parent=current_state,
                                   symbol=char)
                self._counter += 1
                current_state.transitions[char] = next_state
                current_state = next_state
        current_state.success = True
        current_state.matched_keyword = original_keyword

    def search(self, text):
        '''
        Alias for the search_one method
        '''
        return self.search_one(text)

    def search_one(self, text):
        '''
        Search a text for any occurence of any added keyword.
        Returns when one keyword has been found.
        Can only be called after finalized() has been called.
        O(n) with n = len(text)
        @return: 2-Tuple with keyword and startindex in text.
                 Or None if no keyword was found in the text.
        '''
        result_gen = self.search_all(text)
        try:
            return next(result_gen)
        except StopIteration:
            return None

    def search_all(self, text):
        '''
        Search a text for all occurences of the added keywords.
        Can only be called after finalized() has been called.
        O(n) with n = len(text)
        @return: Generator used to iterate over the results.
                 Or None if no keyword was found in the text.
        '''
        if not self._finalized:
            raise ValueError('KeywordTree has not been finalized.' +
                             ' No search allowed. Call finalize() first.')
        if self._case_insensitive:
            text = text.lower()
        current_state = self._zero_state
        for idx, symbol in enumerate(text):
            current_state = current_state.transitions.get(
                symbol, self._zero_state.transitions.get(symbol,
                                                         self._zero_state))
            state = current_state
            while state != self._zero_state:
                if state.success:
                    keyword = state.matched_keyword
                    yield (keyword, idx + 1 - len(keyword))
                state = state.longest_strict_suffix

    def finalize(self):
        '''
        Needs to be called after all keywords have been added and
        before any searching is performed.
        '''
        if self._finalized:
            raise ValueError('KeywordTree has already been finalized.')
        self._zero_state.longest_strict_suffix = self._zero_state
        self.search_lss_for_children(self._zero_state)
        self._finalized = True

    def search_lss_for_children(self, zero_state):
        processed = set()
        to_process = [zero_state]
        while to_process:
            state = to_process.pop()
            processed.add(state.identifier)
            for child in state.transitions.values():
                if child.identifier not in processed:
                    self.search_lss(child)
                    to_process.append(child)

    def search_lss(self, state):
        if state.longest_strict_suffix is None:
            parent = state.parent
            traversed = parent.longest_strict_suffix
            while True:
                if state.symbol in traversed.transitions and\
                        traversed.transitions[state.symbol] != state:
                    state.longest_strict_suffix =\
                        traversed.transitions[state.symbol]
                    break
                elif traversed == self._zero_state:
                    state.longest_strict_suffix = self._zero_state
                    break
                else:
                    traversed = traversed.longest_strict_suffix
            suffix = state.longest_strict_suffix
            if suffix.longest_strict_suffix is None:
                self.search_lss(suffix)
            for symbol, next_state in suffix.transitions.items():
                if (symbol not in state.transitions and
                        suffix != self._zero_state):
                    state.transitions[symbol] = next_state

    def __str__(self):
        return "ahocorapy KeywordTree"

    def __getstate__(self):
        state_list = [None] * self._counter
        todo_list = [self._zero_state]
        while todo_list:
            state = todo_list.pop()
            transitions = {key: value.identifier for key,
                           value in state.transitions.items()}
            state_list[state.identifier] = {
                'symbol': state.symbol,
                'success': state.success,
                'parent':  state.parent.identifier if state.parent is not None else None,
                'matched_keyword': state.matched_keyword,
                'longest_strict_suffix': state.longest_strict_suffix.identifier if state.longest_strict_suffix is not None else None,
                'transitions': transitions
            }
            for child in state.transitions.values():
                if len(state_list) <= child.identifier or not state_list[child.identifier]:
                    todo_list.append(child)

        return {
            'case_insensitive': self._case_insensitive,
            'finalized': self._finalized,
            'counter': self._counter,
            'states': state_list
        }

    def __setstate__(self, state):
        self._case_insensitive = state['case_insensitive']
        self._counter = state['counter']
        self._finalized = state['finalized']
        states = [None] * len(state['states'])
        for idx, serialized_state in enumerate(state['states']):
            deserialized_state = State(idx, serialized_state['symbol'])
            deserialized_state.success = serialized_state['success']
            deserialized_state.matched_keyword = serialized_state['matched_keyword']
            states[idx] = deserialized_state
        for idx, serialized_state in enumerate(state['states']):
            deserialized_state = states[idx]
            if serialized_state['longest_strict_suffix'] is not None:
                deserialized_state.longest_strict_suffix = states[
                    serialized_state['longest_strict_suffix']]
            else:
                deserialized_state.longest_strict_suffix = None
            if serialized_state['parent'] is not None:
                deserialized_state.parent = states[serialized_state['parent']]
            else:
                deserialized_state.parent = None
            deserialized_state.transitions = {
                key: states[value] for key, value in serialized_state['transitions'].items()}
        self._zero_state = states[0]


if __name__ == "__main__":
    kdtree = KeywordTree(case_insensitive=True)
    for i in ["中华人民共和国", "美利坚合众国", "国中", "樱木花道", "赤木晴子", "流川枫", "赤木刚宪"]:
        kdtree.add(i)
    kdtree.finalize()
    sentence = "中华人民共和国简称中国， 最近和美利坚进行贸易战，但是我不care， 我闲暇时候看了看灌南高手，里面的樱木喜欢晴子，晴子仰慕流川枫， 赤木刚宪哈皮"
    results = kdtree.search_all(sentence)
    for result in results:
        print(result)

