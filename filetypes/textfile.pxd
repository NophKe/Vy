from vy.filetypes.basefile cimport BaseFile
from cython import final, locals

#from threading import Thread
#from queue import Queue
cdef object Thread
cdef object Empty
cdef object Queue


cpdef str get_prefix(str token)
cdef str _resolve_prefix(str color_string)

@final
cdef class TextFile(BaseFile):
    cdef:
        object _lex_away_may_run
        object _lex_away_should_stop
        list _lexed_lines
        object _control_queue
        object _lexer_proc 
        object _lexer

    @locals(line=list,
            offset=int,
            tok=object,
            val=str,
            token_line=str,
            line=list)
    cpdef void _lex_away(self)

    @locals(index=int)
    cdef str get_lexed_line(self, int index, bint flash_screen) 
