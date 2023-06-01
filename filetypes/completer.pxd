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
    #settings.add_bracket_after_function = True
    
cdef class Completer:
    cdef list completers
    cdef object buff
        
    cpdef complete(self, int line, int column)
