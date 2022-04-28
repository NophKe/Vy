#from vy.console cimport visit_stdin
from vy.screen cimport Screen 
from vy.interface cimport Interface
from vy.filetypes cimport Open_path

from cython import final, locals

@final
cdef class _Cache:
    cdef dict _dic
    cdef int _counter
    cdef object _make_key(self, object key)

@final
cdef class _Actions:
    cdef public dict insert
    cdef public dict normal
    cdef public dict command
    cdef public dict visual
#
@final
cdef class _Register:
    cdef dico

@final
cdef class _Editor:
    cdef public object input_thread
    cdef public object print_thread
    cdef:
        #dict __dict__
        bint _async_io_flag
        object _input_queue
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
    @locals(rv=str,
            key_press=str) 
    cpdef str read_stdin(self)
    cpdef void edit(self, buff)
    cpdef void push_macro(self,str string)
    cpdef void warning(self,str msg)
    cpdef void edit(self, location)
    cpdef void start_async_io(self)
    cpdef void stop_async_io(self)
    @locals(old_screen=list,
            new_screen=list,
            filtered=list,
            index=Py_ssize_t,
            to_print=str,
            line=str,
            old_line=str
            )
    cpdef void print_loop(self)
    cpdef void input_loop(self)
