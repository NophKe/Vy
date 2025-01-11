from vy.utils import Cancel
from threading import Thread

import re

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self, text=None):
        self.root = TrieNode()
        if text:
            # Extract words from the text using a regular expression
            words = re.findall(r'\b\w+\b', text)
            for word in words:
                self.insert(word)

    def insert(self, word: str):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def search(self, word: str) -> bool:
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word

    def starts_with(self, prefix: str) -> bool:
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

    def _collect_words(self, node, prefix, words):
        if node.is_end_of_word:
            words.append(prefix)
        for char, child in node.children.items():
            self._collect_words(child, prefix + char, words)

    def __iter__(self):
        words = []
        self._collect_words(self.root, '', words)
        return iter(words)
    
class Completer:
    def __init__(self, buffer):
        self.buff = buffer
        self.selected = -1
        self.completion = []
        self.prefix_len = 0
        
        self._async = Cancel()    
        self._last = (0,0)
        self.last_version = None
        
#        Thread(target=self.generate, args=(),daemon=True).start()
        
    @property
    def is_active(self):
        return self._async.task_done and self.completion and self.selected != -1
               
    def generate(self):
        while True:     
            self._async.notify_working()
            (lin, col), version = self.buff.cursor_lin_col, self.buff.string
            if self.last_version is not version:
                self.last_version = version
            
#            raise RuntimeError
            result, prefix = self.buff.auto_complete()
            if result:
                self.completion, self.prefix_len = result, prefix
                self.selected = -1
            
            self._async.notify_task_done()
            self.selected = -1
            self.completion = []
            self.prefix_len = 0
                
    def get_raw_screen(self):
        if self.buff._cursor_lin_col != self._last:
            self._last = self.buff.cursor_lin_col
            self._async.restart_work()
        if self._async.task_done:
            return self.completion, self.selected
        return [], -1
        
    def move_cursor_up(self):
        if self.selected > 0:
            self.selected -= 1
        else:
            self.selected = len(self.completion) - 1

    def move_cursor_down(self):
        if self.selected == len(self.completion) - 1:
            self.selected = 0
        else:
            self.selected += 1

    def select_item(self):
        if self.is_active:
            return self.completion[self.selected], self.prefix_len
        return '', 0

