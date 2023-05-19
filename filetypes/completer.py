from vy.global_config import DONT_USE_JEDI_LIB
from re import split

make_word_set = lambda string: set(split(r'[{}\. :,()\[\]]|$', string))
ANY_BUFFER_WORD_SET = set()

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
    #settings.add_bracket_after_function = True
    
    class ScriptCompleter(Script):
        def complete(self, line, column):
            completion = super().complete(line=line, column=column)
            if completion:
                lengh = completion[0].get_completion_prefix_length()
                return [item.name_with_symbols for item in completion if hasattr(item, 'name_with_symbols')], lengh 

except ImportError:
    ScriptCompleter = None

class Completer:
    def __init__(self, buffer):
        self.completers = []
        if ScriptCompleter:
            if buffer.path.name.lower().endswith('py'):
                self.completers.append(ScriptCompleter(code=buffer.string))
        self.completers.append(WordCompleter(buffer))
        self.buff = buffer
        
    def complete(self, line, column):
        for completer in self.completers:
            if (completion := completer.complete(line=line, column=column)):
                return completion

