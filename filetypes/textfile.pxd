from vy.filetypes.basefile cimport BaseFile
from vy.filetypes.lexer import get_prefix
from vy.filetypes.lexer cimport get_prefix
from vy.filetypes.completer cimport Completer

from cython import final, locals

#from .threading import Thread, Event
from threading import Thread, Event
from time import sleep

cdef dict colorscheme
cdef dict codes

#@final
cdef class TextFile(BaseFile):
    cdef:
        public Completer completer_engine
        public list _lexed_lines
        public dict _lexed_cache
        public list _token_list
        
    cpdef void _lex_away(self) noexcept
    cpdef get_completions(self) noexcept
    cpdef tuple get_raw_screen(self, int min_lin, int max_lin)
