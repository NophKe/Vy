from time import sleep
from threading import Thread, Event
from queue import Queue

from vy.filetypes.basefile import BaseFile
from vy import global_config

try:
    from jedi import Script
    JEDI_INSTALLED = True
except ImportError:
    JEDI_INSTALLED = False

try:
    if global_config.DONT_USE_PYGMENTS_LIB:
        raise ImportError
    from pygments.lexers import guess_lexer_for_filename as guess_lexer
    from pygments.util import ClassNotFound
    from pygments.token import (Keyword, Name, Comment, 
                                String, Error, Number, Operator, 
                                Generic, Token, Whitespace, Text)
    colorscheme = {
      '':                 '',
      Token:              '',
      Whitespace:         '',             Comment:            '/gray/',
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
        for ttype in repr(token).split('.'):
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
        self._lex_away_may_run = Event()
        self._lex_away_should_stop = Event()
        self._lexer_waiting = Event()

        self._lexed_lines = list()

        self.pre_update_callbacks.append(self._lex_away_may_run.clear)
        self.pre_update_callbacks.append(self._lex_away_should_stop.set)
        self.pre_update_callbacks.append(self._lexer_waiting.wait)
        self.pre_update_callbacks.append(self._lexer_waiting.clear)

        
        self.update_callbacks.append(self._lex_away_should_stop.clear)
        self.update_callbacks.append(self._lex_away_may_run.set)

        if global_config.DONT_USE_PYGMENTS_LIB:
            self._lexer = None
        else:
            try:
                self._lexer = guess_lexer(str(self.path), self._string).get_tokens_unprocessed
            except ClassNotFound:
                self._lexer = None
        
        self._lexer_proc = Thread(target=self._lex_away, daemon=True)
        self._lexer_proc.start()
        self._lexer_waiting.wait()
        self._lex_away_may_run.set()

        self._complete_flag = False
        if JEDI_INSTALLED:
            if self.path:
                if self.path.name.lower().endswith('.py'):
                    self._complete_flag = True

        self._completer = None, None

    @property
    def completer_engine(self):
        with self._lock:
            _, version = self._completer
            if version != self._string:
                self._completer = Script(code=self.string), self.string
            return self._completer[0]

    def check_completions(self):
        _, version = self._completer
        if self._string == version and self.cursor_lin_col == self._last_comp:
            return False
        return True

    def get_completions(self):
        if self._complete_flag and JEDI_INSTALLED:
            with self._lock:
                lin, col = self.cursor_lin_col
                self._last_comp = lin, col
                completions = self.completer_engine.complete(line=lin+1, column=col-1)
                if completions:
                    lengh = completions[0].get_completion_prefix_length()
                    return [item.name_with_symbols for item in completions if hasattr(item, 'name_with_symbols')], lengh 
        return [], 0

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
            self._lexer_waiting.set()
            self._lex_away_may_run.wait()
            if self._lex_away_should_stop.wait(0.04):
                continue
            with self._lock:
                self.splited_lines
                self.cursor_lin_col
                self.number_of_lin
                local_str = self.string
                if self._lex_away_should_stop.wait(0.04):
                    continue
                local_lexer = self.lexer()
                line = ''
                local_lexed = list()

                for _, tok, val in local_lexer:
                    if self._lex_away_should_stop.is_set():
                        break
                    tok = get_prefix(tok)
                    if '\n' in val:
                        for token_line in val.splitlines(True):
                            if self._lex_away_should_stop.is_set():
                                break
                            if token_line.endswith('\n'):
                                line += tok + token_line[:-1] + ' \x1b[0m'
                                local_lexed.append(line)
                                line = ''
                            else:
                                line += tok + token_line + '\x1b[0m'
                                #line += f'{tok}{token_line}\x1b[0m'
                    else:
                        line += tok + val + '\x1b[0m'
                else:
                    if line: #No eof
                        local_lexed.append(line)
                    self._lexed_lines = local_lexed
            self._lex_away_should_stop.wait()
            self._lexed_lines.clear()

    def get_raw_screen(self, min_lin, max_lin):
        raw_line_list = list()

        try:
            cursor_lin, cursor_col = self._cursor_lin_col
        except ValueError:
            raise RuntimeError # _cusor_lin_col got invalidated

        if self._lexed_lines:
            local_lexed = self._lexed_lines
        elif self._splited_lines:
            local_lexed = self._splited_lines
        else:
            sleep(0)
            if self._splited_lines:
                local_lexed = self._splited_lines
            else:
                raise RuntimeError # buffer in inconsistant state

        try:
            for on_lin in range(min_lin, max_lin):
                raw_line_list.append(local_lexed[on_lin].replace('\n', ' '))
        except IndexError:
            # check if number_of_lin is valid first
            if self._number_of_lin and self._number_of_lin <= on_lin:
                for _ in range(on_lin, max_lin):
                    raw_line_list.append(None)
            else:
                raise RuntimeError # local_lexed got .clear() by other thread

        return cursor_lin, cursor_col, raw_line_list
