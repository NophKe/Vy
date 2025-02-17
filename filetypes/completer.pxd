from vy.global_config import DONT_USE_JEDI_LIB

from re import split
from jedi import Script, settings


cdef class Completer:
    cdef object buff
    cdef public int selected
    cdef list completers
    cdef list completion
    cdef int prefix_len
    cdef object _async
    cdef object _last
    cdef object last_version
    
    cpdef get_raw_screen(self)
