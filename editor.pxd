from vy.console cimport get_a_key
from vy.screen cimport Screen 
from vy.interface cimport Interface

cdef class _Cache:
    cdef dict _dic
    cdef int _counter
    cdef object _make_key(self, object key)

cdef class _Actions:
    cdef public dict insert
    cdef public dict normal
    cdef public dict command
    cdef public dict visual
#
cdef class _Register:
    cdef dico

cdef class _Editor:
    cdef:
        #dict __dict__
        public _Cache cache
        public Screen screen
        public _Actions actions
        public _Register registr
        Interface interface
        object command_line
        str _macro_keys
        bint _running
        list _work_stack
        list command_list
        public str current_mode

    cpdef str read_stdin(self)
    cpdef void edit(self, buff)
    cpdef void push_macro(self,str string)
    cpdef void warning(self,str msg)
    cpdef void edit(self, location)
    #cpdef show_screen(self, bint renew=*)
