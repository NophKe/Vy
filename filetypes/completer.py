from vy.global_config import DONT_USE_JEDI_LIB

from re import split

make_word_set = lambda string: set(split(r'[{}\. :,()\[\]]|$', string))
make_word_list = lambda string: split(r'[{}\. :,()\[\]!%\*\?=]', string)

ANY_BUFFER_WORD_SET = set()
ANY_BUFFER_LINE_SET = set()

class WordCompleter:
    def __init__(self, code='', **kwargs):
        self.words = set()
        self.split = code.splitlines()
        for line in self.split:
            for w in make_word_set(line):
                ANY_BUFFER_WORD_SET.add(w)
                self.words.add(w)

    def complete(self,line, column):
        word_list = make_word_list(self.split[line-1 if line else 0][:column+1])
        if len(word_list) >= 2:
            word = word_list[-2]
            prefix_len = len(word)
            if prefix_len:
                rv = [item for item in self.words if item.startswith(word)]
                if not rv:
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
            return WordCompleter(code=self._code).complete(line=line, column=column)

except ImportError:
    ScriptCompleter = WordCompleter
