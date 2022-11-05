# For typing definitions
from vy cimport keys as k
from vy.editor cimport _Editor
from vy.screen cimport Screen
from vy.filetypes.basefile cimport DummyLine
from vy.interface.helpers cimport one_inside_dict_starts_with, Completer

# Cython declaration utils
from cython cimport final, locals

cdef object Path

# Module content definition
@final

cdef Completer readline 

@locals(ARG=str,
        PART=str,
        REG=str,
        cmd=str,
        user_input=str,
        action=object)
cpdef str loop(_Editor self)
