from vy.global_config import DONT_USE_JEDI_LIB

from re import split
from jedi import Script, settings

cdef set make_word_set(str string) noexcept
cdef set ANY_BUFFER_WORD_SET

cdef class WordCompleter:
    cdef object buff
    cdef set words
    cdef list split
    
    cpdef tuple complete(self, int line, int column)
    
cdef class Completer:
    cdef object buff
    cdef int selected
    cdef list completers
    cdef list completion
    cdef int prefix_len
    cdef object _async
    cdef object _last
    cdef object last_version
    
    cpdef get_raw_screen(self)
