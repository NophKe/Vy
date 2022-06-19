from time import sleep
from threading import Thread, Condition, Event
from queue import Queue, Empty

from vy.filetypes.basefile import BaseFile
from vy import global_config

try:
    if global_config.DONT_USE_PYGMENTS_LIB:
        raise ImportError
    from pygments.lexers import guess_lexer_for_filename as guess
    from pygments.util import ClassNotFound
    from pygments.token import (Keyword, Name, Comment, 
                                String, Error, Number, Operator, 
                                Generic, Token, Whitespace, Text)
    colorscheme = {
      '':                 '',
      Token:              '',
      Whitespace:         'gray',         Comment:            '/gray/',
      Comment.Preproc:    'cyan',         Keyword:            '*blue*',
      Keyword.Type:       'cyan',         Operator.Word:      'magenta',
      Name.Builtin:       'cyan',         Name.Function:      'green',
      Name.Namespace:     '_cyan_',       Name.Class:         '*green*',
      Name.Exception:     'cyan',         Name.Decorator:     'brightblack',
      Name.Variable:      'red',          Name.Constant:      'red',
      Name.Attribute:     'cyan',         Name.Tag:           'brightblue',
      String:             'yellow',       Number:             '*blue*',
      Generic.Deleted:    'brightred',    Text:               '',
      Generic.Inserted:   'green',        Generic.Heading:    '**',
      Generic.Subheading: '*magenta*',    Generic.Prompt:     '**',
      Generic.Error:      'brightred',    Error:              '_brightred_',
    }
except ImportError:
    global_config.DONT_USE_PYGMENTS_LIB = True
    colorscheme = {'': ''}

codes = {
        ""          : "",
# Text Formatting Attributes
        "reset"     : "\x1b[39;49;00m", "bold"      : "\x1b[01m",
        "faint"     : "\x1b[02m",       "standout"  : "\x1b[03m",
        "underline" : "\x1b[04m",       "blink"     : "\x1b[05m",
        "overline"  : "\x1b[06m",
# Dark Colors
        "black"     :  "\x1b[30m",      "red"       :  "\x1b[31m",
        "green"     :  "\x1b[32m",      "yellow"    :  "\x1b[33m",
        "blue"      :  "\x1b[34m",      "magenta"   :  "\x1b[35m",
        "cyan"      :  "\x1b[36m",      "gray"      :  "\x1b[37m",
# Light Colors
        "brightblack"   :  "\x1b[90m",  "brightred"     :  "\x1b[91m",
        "brightgreen"   :  "\x1b[92m",  "brightyellow"  :  "\x1b[93m",
        "brightblue"    :  "\x1b[94m",  "brightmagenta" :  "\x1b[95m",
        "brightcyan"    :  "\x1b[96m",  "white"         :  "\x1b[97m",
    }

def get_prefix(token):
    try:
        return colorscheme[token]
    except KeyError:
        accu = ''
        for ttype in token.split('.'):
            if ttype in colorscheme:
                colorscheme[token] = colorscheme[ttype]
            accu = f'{accu}{"." if accu else ""}{ttype}'
            if accu in colorscheme:
                colorscheme[token] = colorscheme[accu]
    return colorscheme[token]

def _resolve_prefix(color_string):
    result: str = ''
    if color_string[:1] == color_string[-1:] == '/':
        result += "\x1b[02m"
        color_string = color_string[1:-1]
    if color_string[:1] == color_string[-1:] == '*':
        result += "\x1b[01m"
        color_string = color_string[1:-1]
    if color_string[:1] == color_string[-1:] == '_':
        result += "\x1b[04m"
        color_string = color_string[1:-1]
    result += codes[color_string]
    return result

colorscheme = {repr(key): _resolve_prefix(value) for key, value in colorscheme.items()}

class TextFile(BaseFile):
    """This is the class that most of files buffers should use, 
    and should be preferably yielded by editor.cache[].
    Inherit from it to customize it.
    """
    modifiable = True
    def __init__(self, *args, **kwargs):
        BaseFile.__init__(self, *args, **kwargs)

        #self._lex_away_waiting = Event()
        #self._lex_away_waiting.set()
        self._lex_away_may_run = Event()
        self._lex_away_should_stop = Event()
        self._lexed_lines = list()

        self.pre_update_callbacks.append(self._lex_away_may_run.clear)
        self.pre_update_callbacks.append(self._lex_away_should_stop.set)

        #self.update_callbacks.append(self._lex_away_waiting.wait)
        self.update_callbacks.append(self._lex_away_should_stop.clear)
        self.update_callbacks.append(self._lex_away_may_run.set)

        if global_config.DONT_USE_PYGMENTS_LIB:
            self._lexer = None
        else:
            try:
                self._lexer = guess(str(self.path), self._string).get_tokens_unprocessed
            except ClassNotFound:
                self._lexer = None
        self._lex_away_may_run.set()
        self._lexer_proc = Thread(target=self._lex_away, daemon=True)
        self._lexer_proc.start()

    def lexer(self):
            if self._lexer is None:
                yield from [ (0, '', f'\x1b[33m{val}\x1b[0m') 
                                if val.startswith('#')
                            else (0, '', val)
                    for val in self.splited_lines]
            else:
                    yield from self._lexer(self.string)

    def _lex_away(self):
        while True:
            self._lex_away_may_run.wait()
            line = list()
            self._lexed_lines.clear()
            sleep(0.04) #like eternity.... syntax coloring should never go first
            if not (rv := self._lock.acquire()):
                raise BaseException(f'{rv =}')
            for _, tok, val in self.lexer():
                if self._lex_away_should_stop.is_set():
                    self._lock.release()
                    break
                tok = get_prefix(repr(tok))
                if '\n' in val:
                    for token_line in val.splitlines(True):
                        if token_line.endswith('\n'):
                            token_line = token_line[:-1] + ' '
                            line.append(f'{tok}{token_line}\x1b[0m')
                            self._lexed_lines.append(''.join(line))
                            line.clear()
                        else:
                            line.append(f'{tok}{token_line}\x1b[0m')
                else:
                    line.append(f'{tok}{val}\x1b[0m')
            else:
                if line: #No eof
                    self._lexed_lines.append(line)
                self._lock.release()
                self._lex_away_should_stop.wait()

    def get_lexed_line(self, index, flash_screen):
        try:
            return self._lexed_lines[index]
        except IndexError:
            if flash_screen:
                try:
                    return self._splited_lines[index].replace('\n', ' ')
                except IndexError:
                    raise RuntimeError
            elif self.number_of_lin > index >= 0:
                try:
                    return self._lexed_lines[index]
                except IndexError:
                    return self.splited_lines[index].replace('\n', ' ')
            raise
