from time import sleep
from threading import Thread, Event
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

        self._screen_can_visit_lexed = Event()
        self._screen_can_visit_spl = Event()
        self._lex_away_may_run = Event()
        self._lex_away_may_run.set()
        self._lex_away_should_stop = Event()
        self._lexed_lines = list()

        self.pre_update_callbacks.append(self._lex_away_may_run.clear)
        self.pre_update_callbacks.append(self._lex_away_should_stop.set)
        self.pre_update_callbacks.append(self._screen_can_visit_spl.clear)
        self.pre_update_callbacks.append(self._screen_can_visit_lexed.clear)

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
        #self._lex_away_may_run.set()
        self._lexer_proc = Thread(target=self._lex_away, daemon=True)
        self._lex_away_may_run.set()
        self._lexer_proc.start()

    def lexer(self):
            if self._lexer is None:
                yield from ((0, '', f'\x1b[33m{val}\x1b[0m') 
                                if val.startswith('#')
                            else (0, '', val)
                    for val in self.splited_lines)
            else:
                    yield from self._lexer(self.string)

    def _lex_away(self):
        while True:
            self._lex_away_may_run.wait()
            with self._lock:
                #if not self._screen_can_visit_spl.is_set():
                self.splited_lines
                self.number_of_lin
                self.cursor_lin_col
                self._screen_can_visit_spl.set()

                line = list()
                #count = 0

                self._lexed_lines.clear()

                for _, tok, val in self.lexer():
                    tok = get_prefix(repr(tok)) # old, bad, too early, premature optimization
                    if '\n' in val:
                        if self._lex_away_should_stop.is_set():
                            break
                        for token_line in val.splitlines(True):
                            if token_line.endswith('\n'):
                                line.append(f'{tok}{token_line[:-1]} \x1b[0m')
                                self._lexed_lines.append(''.join(line))
                                line.clear()
                            else:
                                line.append(f'{tok}{token_line}\x1b[0m')
                    else:
                        line.append(f'{tok}{val}\x1b[0m')
                else:
                    if line: #No eof
                        self._lexed_lines.append(line)
                if not self._lex_away_should_stop.is_set():
                    self._screen_can_visit_lexed.set()
            self._lex_away_should_stop.wait()

    #def _list_suppr(self):
        #BaseFile._list_suppr(self)
        #self._screen_can_visit_spl.set()
#
    #def _list_insert(self, value):
        #BaseFile._list_insert(self, value)
        #self._screen_can_visit_spl.set()

    def get_raw_screen(self, min_lin, max_lin):
        #self._lex_away_may_run.wait()

        if self._screen_can_visit_lexed.is_set() and self._screen_can_visit_spl.is_set():
            lexed_lines = self._lexed_lines
        elif self._screen_can_visit_spl.is_set():
            lexed_lines = self._splited_lines
        else:
            sleep(0)
            raise RuntimeError

        #if self._lex_away_should_stop.is_set():
            #raise RuntimeError

        raw_line_list = list()

        try:
            cursor_lin, cursor_col = self._cursor_lin_col
        except ValueError:
            raise RuntimeError

        if not (nb_lines := self._number_of_lin):
            raise RuntimeError


        for on_lin in range(min_lin, max_lin):
            try:
                raw_line_list.append(lexed_lines[on_lin].replace('\n', ' '))
            except IndexError:
                if nb_lines <= on_lin:
                    for _ in range(on_lin, max_lin):
                        raw_line_list.append(None)
                    return cursor_lin, cursor_col, raw_line_list
                else:
                    raise RuntimeError

        return cursor_lin, cursor_col, raw_line_list
