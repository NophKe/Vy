from vy.filetypes.basefile cimport BaseFile
from vy.filetypes.lexer import get_prefix
from vy.filetypes.lexer cimport get_prefix
from vy.filetypes.completer cimport Completer

from cython import final, locals

from threading import Thread
from time import sleep

cdef class TextFile(BaseFile):
    cdef:
        public list _lexed_lines
        public dict _lexed_cache
        public list _token_list
        
    cpdef void _lex_away(self) noexcept
    cpdef tuple get_raw_screen(self, int min_lin, int max_lin)
