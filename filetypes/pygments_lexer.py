""" the codes dict and ansiformat function is freely adapated from
    pygments in the console submodule
    :copyright: Copyright 2006-2020 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from ..global_config import DONT_USE_PYGMENTS_LIB
if DONT_USE_PYGMENTS_LIB: raise ImportError

from .motions import Motions

from pygments.token import (Keyword, Name, Comment, 
                            String, Error, Number, Operator, 
                            Generic, Token, Whitespace, Text)
from pygments.lexers import guess_lexer_for_filename as guess_lexer
from pygments.util import  ClassNotFound


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

#codes["white"] = codes["bold"]

def ansiformat(attr, text):
    """
    Format ``text`` with a color and/or some attributes::

        color       normal color
        *color*     bold color
        _color_     underlined color
        /color/     faint color
    """
    result = ''
    if attr[:1] == attr[-1:] == '/':
        result += "\x1b[02m"
        attr = attr[1:-1]
    if attr[:1] == attr[-1:] == '*':
        result += "\x1b[01m"
        attr = attr[1:-1]
    if attr[:1] == attr[-1:] == '_':
        result += "\x1b[04m"
        attr = attr[1:-1]
    result += codes[attr] + text + "\x1b[0m"
    return result

colorscheme = {
    Token:              '',
    Whitespace:         'gray',         Comment:            '/gray/',
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

class view(Motions):
    @property
    def lexer(self):
        try:
            return self._lexer.get_tokens_unprocessed(self._string)
        except AttributeError:
            try:
                self._lexer = guess_lexer(str(self.path), self._string, 
                                    tabsize = self.set_tabsize, encoding='utf-8')
            except ClassNotFound:
                self._lexer = guess_lexer('text.txt', self._string, 
                                    tabsize = self.set_tabsize, encoding='utf-8')

            return self.lexer

    @property
    def lexed_lines(self):
        if not hasattr(self,'_lexed_hash')  or self._lexed_hash != self._string.__hash__():
            retval = list()
            line = ''
            for offset, tok, val in self.lexer:
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
