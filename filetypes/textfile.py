from vy.filetypes.basefile import BaseFile
from vy.screen import get_prefix

from multiprocessing import Process, Manager, Queue
# TODO should better use futures object than reimplement
# single value processing

def set_lexer(buffer, path):
    from vy.global_config import DONT_USE_PYGMENTS_LIB
    if DONT_USE_PYGMENTS_LIB:
        return lambda: [(0, '', val) for val in buffer._string.splitlines(True)]
    from pygments.lexers import guess_lexer_for_filename as guess_lexer
    from pygments.util import  ClassNotFound
    try:
        _lexer = guess_lexer(str(path), buffer._string).get_tokens_unprocessed
    except ClassNotFound:
        _lexer = guess_lexer('text.txt', buffer._string).get_tokens_unprocessed
    return lambda : _lexer(buffer._string)

class TextFile(BaseFile):
    """This is the class that most of files buffers should use, 
    and should be preferably yielded by editor.cache[].
    Inherit from it to customize it.
    there should be a callback register to come.
    """
    modifiable = True
    def __init__(self, *args, **kwargs):
        self.PROC = None
        self.lexer = None
        super().__init__(self, *args, **kwargs)

    def update_properties(self):
        if self.lexer is None:
            self.lexer = set_lexer(self, self.path) 
        self._lexed_lines = list()

    def get_lexed_line(self, index):
        lexed_string = ''
        line = self.lexed_lines[index]
        for text, token in line:
            lexed_string = f'{lexed_string}{get_prefix(token)}{text}\x1b[0m'
        return index, lexed_string
    
    @property
    def lexed_lines(self) :
        if not self._lexed_lines:
            retval = list()
            line = list()
            for offset, tok, val in self.lexer():
                if '\n' in val:
                    for token_line in val.splitlines(True):
                        if token_line.endswith('\n'):
                            token_line = token_line[:-1] + ' '
                            line.append((token_line, repr(tok)))
                            retval.append(line)
                            line = list()
                        else:
                            line.append((token_line, repr(tok)))
                else:
                    line.append((val, repr(tok)))
            if line: #No eof
                retval.append(line)
            self._lexed_lines = retval
        return self._lexed_lines
