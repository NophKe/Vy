import re
from re import split as re_split
from token import EXACT_TOKEN_TYPES
from keyword import iskeyword, issoftkeyword
import builtins

VULGAR = ('TODO', 'FIXME', 'FUCK')

tokenize = ( '('
           + r'\b|'
           + r'\d+|'
           + r"'[^']*'|"
           + r'"[^"]*"|'
           + r'__[^_]*__|'
           + '|'.join(map(re.escape, EXACT_TOKEN_TYPES))
           + '|'.join(VULGAR)
           + ')'
           )

from vy.global_config import DONT_USE_PYGMENTS_LIB

def guess_lexer_base(path_str, code_str):
    if path_str.lower().endswith('.py'):
        return py_lexer
    if path_str.lower().endswith('.c'):
        return py_lexer
    return txt_lexer

def txt_lexer(string):
    for line in string.splitlines(True):
        yield 0, '', line

def py_lexer(string):
    for line in string.splitlines(True):
        if line.strip().startswith('#') and line.endswith('\n'):
            yield 0, 'Comment', line
            continue
        for it in re_split(tokenize, line):
            if not it:
                continue
            elif not it.strip():
                for sub_space in re.split('(\t+|\\s+\n)', it):
                    if '\t' in sub_space:
                        yield 0, 'Important', sub_space
                    elif len(sub_space) != 1 and sub_space.endswith('\n'):
                        yield 0, 'Empty', sub_space
                    else:
                        yield 0, '', sub_space
            elif it.isdigit():
                yield 0, 'Number', it
            elif iskeyword(it) or issoftkeyword(it):
                yield 0, 'Keyword', it
            elif it in EXACT_TOKEN_TYPES:
                yield 0, 'Operator', it
            elif it in dir(builtins):
                yield 0, 'Name.Builtin', it
            elif it[0] == it[-1] and it[0] in '\'"':
                yield 0, 'String', it
            elif it[0] == it[-1] and it[0] in '_':
                yield 0, 'Important', it
            elif it == 'self':
                yield 0, 'Operator', it
            elif it in VULGAR:
                yield 0, 'Important', it
            else:
                yield 0, '', it

try:
    if DONT_USE_PYGMENTS_LIB:
        raise ImportError
    from pygments.lexers import guess_lexer_for_filename
    from pygments.util import ClassNotFound
    from pygments.token import (Keyword, Name, Comment,
                                String, Error, Number, Operator,
                                Generic, Token, Whitespace, Text, )

    colorscheme = {
      '':                 '',
      Token:              '',
      Whitespace:         '',             Comment:            '/gray/',
      Comment.Preproc:    'cyan',         Keyword:            '*blue*',
      Keyword:            'cyan',         Operator.Word:      'magenta',
      Name.Builtin:       'cyan',         Name.Function:      '*green*',
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
    colorscheme = {
      '':         '',
      'Name.Builtin':       'brightblue',
      'Name.Function':      'green',
      'Keyword':  'cyan',
      'Comment':  '/gray/',
      'Operator': 'brightgreen',
      'Statement': 'cyan',
      'Loop':      '*green*',
      'Title':     '*yellow*',
      'Subtitle':   '*magenta*',
      'String':     'yellow',
      'Number':     '*blue*',
      'Important':  '/*_brightred_*/',
      'Empty':      '/_gray_/',
    }
    DONT_USE_PYGMENTS_LIB = True

def guess_lexer(path, code_str):
    path_str = '' if path is None else str(path)
    if DONT_USE_PYGMENTS_LIB:
        return guess_lexer_base(path_str, code_str)

    try:
        return guess_lexer_for_filename(path_str, code_str).get_tokens_unprocessed
    except ClassNotFound:
        pass
    try:
        return guess_lexer_for_filename('', code_str).get_tokens_unprocessed
    except ClassNotFound:
        pass
    try:
        return guess_lexer_for_filename(path_str, '').get_tokens_unprocessed
    except ClassNotFound:
        return guess_lexer_base(path_str, code_str)


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
        token_str = token if isinstance(token, str) else repr(token)
        accu = ''
        for ttype in token_str.split('.'):
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

