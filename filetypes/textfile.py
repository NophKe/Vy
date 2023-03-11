from threading import Thread, Event

from vy.filetypes.basefile import BaseFile
from vy import global_config

from re import split
make_word_set = lambda string: set(split(r'[{}\. :,()\[\]]|$', string))
make_word_list = lambda string: split(r'[{}\. :,()\[\]]|$', string)

class WordCompleter:
    def __init__(self, code='', **kwargs):
        self.code = code
        self.split = code.splitlines()
        self.words = set()
        for line in self.split:
            for w in make_word_set(line):
                self.words.add(w)
    def complete(self,line, column):
        word_list = make_word_list(self.split[line-1 if line else 0][:column+1])
        if len(word_list) >= 2:
            word = word_list[-2]
            return [item for item in self.words if item.startswith(word) and item != word], len(word)
        return None

try:
    if global_config.DONT_USE_JEDI_LIB:
        raise ImportError
    from jedi import Script, settings
    settings.add_bracket_after_function = True
    
    class ScriptCompleter(Script):
        def complete(self, line, column):
            completion = super().complete(line=line, column=column)
            if completion:
                lengh = completion[0].get_completion_prefix_length()
                return [item.name_with_symbols for item in completion if hasattr(item, 'name_with_symbols')], lengh 
            else:
                return WordCompleter(code=self._code).complete(line=line, column=column)
            return None

except ImportError:
    ScriptCompleter = WordCompleter

def guess_lexer_base(path_str, code_str):
    if path_str.lower().endswith('.py'):
        return py_lexer
    return txt_lexer
 
from keyword import iskeyword
import tokenize

class line_reader:
    def __init__(self, string):
        self.list = string.splitlines(True)
        self.list.reverse()
    def __call__(self):
        return self.list.pop()
        
def py_lexer(string):
    for line in string.splitlines(True):
        if line.lstrip().startswith('#'):
            yield 0, 'Comment', line
        else:
            word = ''
            for char in line:
                word += char
                if iskeyword(word):
                    yield 0, 'Keyword', word
                    word = ''
                elif not char.isalpha():
                    yield 0, '', word
                    word = ''
            else:
                if word:
                    yield 0, '', word

def py_lexer(string):
    for ttype, val, _, _, _ in tokenize.tokenize(line_reader(string)):
        yield 0, ttype, val
    

def txt_lexer(string):
    for line in string.splitlines(True):
        yield 0, '', line

try:
    if global_config.DONT_USE_PYGMENTS_LIB:
        raise ImportError
    from pygments.lexers import guess_lexer_for_filename
    from pygments.util import ClassNotFound
    from pygments.token import (Keyword, Name, Comment, 
                                String, Error, Number, Operator, 
                                Generic, Token, Whitespace, Text)
    def guess_lexer(*args):
        try:
            return guess_lexer_for_filename(*args).get_tokens_unprocessed
        except ClassNotFound:
            return guess_lexer_base(*args)
            
    colorscheme = {
      '':                 '',
      Token:              '',
      Whitespace:         '',             Comment:            '/gray/',
      Comment.Preproc:    'cyan',         Keyword:            '*blue*',
      Keyword.Type:       'cyan',         Operator.Word:      'magenta',
      Name.Builtin:       'cyan',         Name.Function:      'green',
      Name.Namespace:     '*cyan*',       Name.Class:         '*green*',
      Name.Exception:     'cyan',         Name.Decorator:     'brightblack',
      Name.Variable:      'red',          Name.Constant:      'red',
      Name.Attribute:     'cyan',         Name.Tag:           'brightblue',
      String:             'yellow',       Number:             '*blue*',
      Generic.Deleted:    'brightred',    Text:               '',
      Generic.Inserted:   'green',        Generic.Heading:    '**',
      Generic.Subheading: '*magenta*',    Generic.Prompt:     '**',
      Generic.Error:      'brightred',    Error:              '*brightred*',
    }
except ImportError:
    global_config.DONT_USE_PYGMENTS_LIB = True
    colorscheme = {
      '':         '',
      'Keyword':  '*blue*',
      'Comment':  '/gray/'
    }
    guess_lexer = guess_lexer_base


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
        if not isinstance(token, str):
            it = repr(token)
        else:
            it = token
        accu = ''
        for ttype in it.split('.'):
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

colorscheme = {str(key): _resolve_prefix(value) for key, value in colorscheme.items()}

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

        self._lexed_cache = {}
        self._lexed_lines = list()

        self.pre_update_callbacks.append(self._lex_away_may_run.clear)
        self.pre_update_callbacks.append(self._lex_away_should_stop.set)
        
        self.update_callbacks.append(self._lex_away_should_stop.clear)
        self.update_callbacks.append(self._lex_away_may_run.set)

        self.lexer = guess_lexer(str(self.path), self._string)
        
        self._lexer_proc = Thread(target=self._lex_away, daemon=True)
        self._lexer_proc.start()
        self._lex_away_may_run.set()
        self._completer = None, None

    def _make_completer(self):
        if self.path:
            if self.path.name.lower().endswith('.py'):
                return ScriptCompleter(code=self.string, path=self.path)
        return WordCompleter(code=self.string, path=self.path)

    @property
    def completer_engine(self):
        with self._lock:
            _, version = self._completer
            if version != self._string:
                self._completer = self._make_completer(), self.string
            return self._completer[0]

    def check_completions(self):
        _, version = self._completer
        if self._string == version and self.cursor_lin_col == self._last_comp:
            return False
        return True

    def get_completions(self):
        with self._lock:
            lin, col = self.cursor_lin_col
            self._last_comp = lin, col
            completions = self.completer_engine.complete(line=lin+1, column=col-1)
            if completions:
                return completions
            else:
                return [], 0

    def _lex_away(self):
        while True:
            self._lex_away_may_run.wait()
            if self._lex_away_should_stop.wait(0.04):
                continue
            with self._lock:
                local_split = self.splited_lines
                self.cursor_lin_col
                self.number_of_lin
                if self._lex_away_should_stop.wait(0.04):
                    continue
                local_lexer = self.lexer(self.string)
                line = ''
                local_lexed = list()
                count = 0
                local_dict = self._lexed_cache

                for _, tok, val in local_lexer:
                    if self._lex_away_should_stop.is_set():
                        break
                    tok = get_prefix(tok)
                    if '\n' in val:
                        for token_line in val.splitlines(True):
                            if self._lex_away_should_stop.is_set():
                                break
                            if token_line.endswith('\n'):
                                line += tok + token_line[:-1] + ' \x1b[39;49;21;22;24m'
                                local_lexed.append(line)
                                local_dict[local_split[count]] = line
                                count += 1
                                line = ''
                            else:
                                line += tok + token_line + '\x1b[39;49;00;21;22;24m'
                    else:
                        line += tok + val + '\x1b[39;49;21;22;24m'
                else:
                    if line: #No eof
                        local_dict[self._splited_lines[count]] = line
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

        if self._splited_lines:
            local_split = self._splited_lines
        else:
            raise RuntimeError # buffer in inconsistant state

        try:
            for on_lin in range(min_lin, max_lin):
                try:
                    cur_lex = self._lexed_lines[on_lin]
                except IndexError: 
                    cur_lin = local_split[on_lin]
                    cur_lex = self._lexed_cache.get(cur_lin, cur_lin.replace('\n',' '))
                raw_line_list.append(cur_lex)
        except IndexError:
            # check if number_of_lin is valid first
            if self._number_of_lin and self._number_of_lin <= on_lin:
                for _ in range(on_lin, max_lin):
                    raw_line_list.append(None)
            else:
                raise RuntimeError # local_lexed or local_split got .clear() by other thread

        return cursor_lin, cursor_col, raw_line_list
