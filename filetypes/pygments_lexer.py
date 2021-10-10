""" the codes dict and ansiformat function is freely adapated from
    pygments in the console submodule
    :copyright: Copyright 2006-2020 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from ..global_config import DONT_USE_PYGMENTS_LIB
if DONT_USE_PYGMENTS_LIB:
    raise ImportError
from .motions import Motions

from pygments.token import (Keyword, Name, Comment, 
                            String, Error, Number, Operator, 
                            Generic, Token, Whitespace, Text)
from pygments.lexers import guess_lexer_for_filename
from pygments.util import  ClassNotFound

SET_DEF = '\x1b[0m'

codes = {
    ""          : "",
# Text Formatting Attributes
    "reset"     : "\x1b[39;49;00m",
    "bold"      : "\x1b[01m",
    "faint"     : "\x1b[02m",
    "standout"  : "\x1b[03m",
    "underline" : "\x1b[04m",
    "blink"     : "\x1b[05m",
    "overline"  : "\x1b[06m",
# Dark Colors
    "black"     :  "\x1b[30m",
    "red"       :  "\x1b[31m",
    "green"     :  "\x1b[32m",
    "yellow"    :  "\x1b[33m",
    "blue"      :  "\x1b[34m",
    "magenta"   :  "\x1b[35m",
    "cyan"      :  "\x1b[36m",
    "gray"      :  "\x1b[37m",
# Light Colors
    "brightblack"   :  "\x1b[90m",
    "brightred"     :  "\x1b[91m",
    "brightgreen"   :  "\x1b[92m",
    "brightyellow"  :  "\x1b[93m",
    "brightblue"    :  "\x1b[94m",
    "brightmagenta" :  "\x1b[95m",
    "brightcyan"    :  "\x1b[96m",
    "white"         :  "\x1b[97m",
}

codes["white"] = codes["bold"]

def colorize(color_key, text):
    return codes[color_key] + text + codes["reset"]

def ansiformat(attr, text):
    """
    Format ``text`` with a color and/or some attributes::

        color       normal color
        *color*     bold color
        _color_     underlined color
        +color+     blinking color
    """
    result = ''
    if attr[:1] == attr[-1:] == '*':
        result += "\x1b[01m"
        attr = attr[1:-1]
    if attr[:1] == attr[-1:] == '_':
        result += "\x1b[04m"
        attr = attr[1:-1]
    result += codes[attr] + text + "\x1b[39;49;00m"
    return result

colorscheme = {
    Token:              '',
    Whitespace:         'gray',         Comment:            'gray',
    Comment.Preproc:    'cyan',         Keyword:            '*blue*',
    Keyword.Type:       'cyan',         Operator.Word:      'magenta',
    Name.Builtin:       'cyan',         Name.Function:      'green',
    Name.Namespace:     '_cyan_',       Name.Class:         '_green_',
    Name.Exception:     'cyan',         Name.Decorator:     'brightblack',
    Name.Variable:      'red',          Name.Constant:      'red',
    Name.Attribute:     'cyan',         Name.Tag:           'brightblue',
    String:             'yellow',       Number:             'blue',
    Generic.Deleted:    'brightred',    Text:               '',
    Generic.Inserted:   'green',        Generic.Heading:    '**',
    Generic.Subheading: '*magenta*',    Generic.Prompt:     '**',
    Generic.Error:      'brightred',    Error:              '_brightred_',
}
#   @cache
def _colorize(ttype):
#       @cache
    def func(text):
        return ansiformat(color, text)
    for token_class in reversed(ttype.split()):
        if ttype in colorscheme:
            color = colorscheme[ttype]
        else:
            ttype = ttype.parent
    return func

def get_rows_needed(number):
    if number < 800:
        return 3
    elif number < 9800:
        return 4
    elif number < 99800:
        return 5
    elif number < 999980:
        return 6
    return len(str(number))

def switch(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
    if on_lin != cursor_lin:
        return expandtabs(tab_size, max_col, text, on_lin, -1 , -1)
    else:
        return expandtabs(tab_size, max_col, text, on_lin, cursor_lin, cursor_col)

def expandtabs(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
    number = str(on_lin).rjust(get_rows_needed(on_lin)) + ': '
    retval = list()
    line  = '\x1b[00;90;40m' + number + SET_DEF

    on_col = len(number) - 1
    cursor_col += on_col - 1
    esc_flag = False
    cursor_flag = False

    for char in text:
        if esc_flag:
            line += char
            if char == 'm':
                esc_flag = False
            continue

        if char == '\x1b':
            esc_flag = True
            line += char
            continue

        if on_col ==  max_col -1:
            line += '\x1b[0m'
            retval.append(line)
            line = '\x1b[90;40m' + ' ' * len(number)+ SET_DEF
            cursor_col -= on_col
            on_col = len(number) -1
            esc_flag = False

        cursor_flag = bool((on_col, on_lin) == (cursor_col, cursor_lin))
        if cursor_flag:
            line += '\x1b[5;7m'

        if char == '\t':
            nb_of_tabs =  tab_size - (on_col % tab_size)
            line += ' ' * nb_of_tabs
            on_col += nb_of_tabs
            cursor_col += (nb_of_tabs-1)
        else:
            on_col += 1
            line += char
        if cursor_flag:
            line += '\x1b[25;27m'

    retval.append(line + (' ' * (max_col - on_col - 1)))
    return retval

class view(Motions):
    def __init__(self, set_wrap=False, set_tabsize=4, **kwargs):
        self.set_wrap = set_wrap
        self.set_tabsize = set_tabsize
        super().__init__(**kwargs)

        filename = self.path if self.path else ''
        try:
            self.lexer = guess_lexer_for_filename(filename, 
                                            self._string, 
                                            tabsize = self.set_tabsize, 
                                            encoding='utf-8')
        except ClassNotFound:
            self.lexer = guess_lexer_for_filename('text.txt', 
                                            self._string, 
                                            tabsize = self.set_tabsize, 
                                            encoding='utf-8')

    def gen_window(self, max_col, min_lin, max_lin):
        cursor_lin, cursor_col = self.cursor_lin_col
        wrap = self.set_wrap
        tab_size = self.set_tabsize
        lexed_lines = self.lexed_lines # Get a copy (descriptor)
        virtuel = 0

        for on_lin in range(min_lin, max_lin):
            try:
                pretty_line = lexed_lines[on_lin]
            except IndexError:
                default = '~' + ((max_col-1) * ' ')
                while True:
                    yield default 
            to_print = switch(tab_size, max_col, pretty_line, on_lin, cursor_lin, cursor_col)
            if wrap: 
                virtuel += len(to_print) 
                free = max_lin - (min_lin + virtuel)
                #if on_lin + free  < cursor_lin + 1:
                #    yield False
                yield from to_print
            else:
                yield to_print[0]

    @property
    def lexed_lines(self):
        if not hasattr(self,'_lexed_hash')  or self._lexed_hash != self._string.__hash__():
            retval = list()
            line = ''
            for offset, tok, val in self.lexer.get_tokens_unprocessed(self._string):
                colorize = _colorize(tok)
                for token_line in val.splitlines(True):
                    if token_line.endswith('\n'):
                        token_line = token_line[:-1] + ' '
                        retval.append(line + colorize(token_line))
                        line = ''
                    else:
                        line += colorize(token_line)
            if line:
                retval.append(line)
            self._lexed_hash, self._lexed_lines = hash(self._string) , retval
        return self._lexed_lines
