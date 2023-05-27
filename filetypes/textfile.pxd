from vy.filetypes.basefile cimport BaseFile
from vy.filetypes.lexer import get_prefix
from vy.filetypes.lexer cimport get_prefix

from cython import final, locals

#from .threading import Thread, Event
from threading import Thread, Event
from time import sleep

cdef dict colorscheme
cdef dict codes

#@final
cdef class TextFile(BaseFile):
    cdef:
        object _last_comp
        tuple _completer
        public list _lexed_lines
        object _lexer_proc 
        object _undo_proc 
        public object lexer
        public dict _lexed_cache
    cpdef void _lex_away(self) noexcept
    cdef check_completions(self) noexcept
    cpdef get_completions(self) noexcept
    cpdef tuple get_raw_screen(self, int min_lin, int max_lin)


