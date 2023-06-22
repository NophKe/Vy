from vy.global_config import DONT_USE_JEDI_LIB

from re import split
from vy.utils import Cancel
from threading import Thread

ANY_BUFFER_WORD_SET = set()

def make_word_set(string):
    return set(split(r'[{}\. :,()\[\]]|$', string))

class WordCompleter:
    def __init__(self, buff):
        self.buff = buff
        self.words = set()
        self.split = buff.string.splitlines()
        for line in self.split:
            for w in make_word_set(line):
                ANY_BUFFER_WORD_SET.add(w)
                self.words.add(w)

    def complete(self,line, column):
        word = self.buff.string[self.buff.find_previous_delim()+1:self.buff.cursor]
        prefix_len = len(word)
        if prefix_len:
            rv = [item for item in self.words if item.startswith(word)]
            if not rv or (len(rv) == 1 and rv[0] == word):
                rv = [item for item in ANY_BUFFER_WORD_SET if item.startswith(word)]
            return rv, prefix_len
        return None

try:
    if DONT_USE_JEDI_LIB:
        raise ImportError
    from jedi import Script, settings
    settings.add_bracket_after_function = True
    settings.case_insensitive_completion = True
    
    class ScriptCompleter(Script):
        def complete(self, line, column):
            try:           
                completion = super().complete(line=line+1, column=column-1)
                lengh = completion[0].get_completion_prefix_length()
                return [item.name_with_symbols for item in completion if hasattr(item, 'name_with_symbols')], lengh 
            except:
                # Jedi Library uses threads and subprocesses. Its use in a
                # multi-threaded application may be unstable, this is inherent
                # to jedi's design, and is well stated in jedi's documentation
                # so we silent any exception.
                return None

except ImportError:
    ScriptCompleter = None

class Completer:
    def __init__(self, buffer):
        self.buff = buffer
        self.selected = -1
        self.completion = []
        self.prefix_len = 0
        self._async = Cancel()    
        self._last = (0,0)
        self.last_version = None
        self.completers = []
        
        if ScriptCompleter:
            if buffer.path and buffer.path.name.lower().endswith('py'):
                self.completers.append(ScriptCompleter(code=buffer.string))
        self.completers.append(WordCompleter(buffer))
        
        Thread(target=self.generate, args=(),daemon=True).start()
        
    @property
    def is_active(self):
        return self._async.task_done and self.completion and self.selected != -1
               
    def generate(self):
        while True:     
            self._async.notify_working()
            (lin, col), version = self.buff.cursor_lin_col, self.buff.string
            if self.last_version is not version:
                self.last_version = version
                self.completers.clear()
                if ScriptCompleter:
                    if self.buff.path and self.buff.path.name.lower().endswith('py'):
                        self.completers.append(ScriptCompleter(code=self.buff.string))
                self.completers.append(WordCompleter(self.buff))
            
            for completer in self.completers:
                if (result := completer.complete(line=lin, column=col)):
                    break
            try:
                self.completion, self.prefix_len = result
            except TypeError:
                self.completion, self.prefix_len = [], 0
                # All completers returned None
            else:
                if self.selected != -1 and len(self.completion):
                    self.selected = 0
            
            self._async.notify_task_done()
#            self.selected = -1
            self.completion = []
            self.prefix_len = 0
                
    def get_raw_screen(self):
        if self.buff._cursor_lin_col != self._last:
            self._last = self.buff.cursor_lin_col
            self._async.restart_work()
        if self._async.task_done:
            return self.completion, self.selected
        
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

