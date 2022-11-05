from vy.filetypes.basefile cimport BaseFile
from cython import final, locals

#from threading import Thread
#from queue import Queue
cdef object Thread
cdef object Empty
cdef object Queue
cdef dict colorscheme
cdef dict codes

#@final
#cdef class IncList(list):
    #pass

@locals( accu=str,
        ttype=str)
cdef str get_prefix(str token)

@locals(result=str)
cdef str _resolve_prefix(str color_string)

@final
cdef class TextFile(BaseFile):
    cdef:
        object _screen_can_visit_lexed
        object _screen_can_visit_spl 
        object _lex_away_may_run 
        object _lex_away_should_stop 
        list _lexed_lines
        object _lexer_proc 
        object _lexer
    #@locals(line=list,
            #offset=int,
            #tok=object,
            #val=str,
            #token_line=str,
            #line=list)
    cpdef void _lex_away(self)
    #cdef void _list_suppr(self)
    #cdef void _list_insert(self, str value)
    #@locals(lexed_lines=list,
            #on_lin=int,
            #nb_lines=int,
            #cursor_lin=int,
            #cursor_col=int)
    cdef tuple get_raw_screen(self, int min_lin, int max_lin)
