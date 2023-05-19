from vy.filetypes.basefile cimport BaseFile
from vy.filetypes.lexer import get_prefix
from vy.filetypes.lexer cimport get_prefix

from cython import final, locals

from threading import Thread

cdef dict colorscheme
cdef dict codes

#@final
cdef class TextFile(BaseFile):
    cdef:
        object _lex_away_may_run 
        object _lex_away_should_stop 
        tuple _completer
        public list _lexed_lines
        object _lexer_proc 
        public object lexer
        public dict _lexed_cache
    cpdef void _lex_away(self)
    cdef check_completions(self)
    cdef get_completions(self)
    cpdef tuple get_raw_screen(self, int min_lin, int max_lin)


