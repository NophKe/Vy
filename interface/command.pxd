from vy.editor cimport Editor
##from vy.console cimport stdout_no_cr, stdin_no_echo_nl
#
cdef class CommandModeCompleter:
    cdef dict __dict__

cpdef str loop(Editor self)
