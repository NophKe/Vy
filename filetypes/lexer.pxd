from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound
from pygments.token import (Keyword, Name, Comment, 
                            String, Error, Number, Operator, 
                            Generic, Token, Whitespace, Text)
from vy import global_config

from keyword import iskeyword
from re import split, sub
import tokenize
import token as py_tokens

cdef object guess_lexer_base(str path_str, str code_str)
cpdef object guess_pygments_lexer(str path_str, str code_str)
cdef dict colorscheme

cpdef guess_lexer(object path, str string)
cdef dict codes
cpdef str get_prefix(object token)
cdef str _resolve_prefix(str color_string)
