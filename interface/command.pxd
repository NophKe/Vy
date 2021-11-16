from vy.editor cimport _Editor
#from vy.interface.helpers cimport CommandCompleter

##from vy.console cimport stdout_no_cr, stdin_no_echo_nl
#
#cdef class CommandModeCompleter(CommandCompleter)

cpdef str loop(_Editor self)
