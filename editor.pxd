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
cdef class NameSpace:
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
    cdef:
        bint _async_io_flag
        bint _running
        #dict __dict__
        Interface interface
        list command_list
        list _work_stack
        object command_line
        object _input_queue
        public _Cache cache
        public NameSpace actions
        public object input_thread
        public object print_thread
        public _Register registr
        public Screen screen
        public str current_mode
        str _macro_keys
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
            to_print=str,
            index=Py_ssize_t,
            new_screen=list,
            filtered=list,
            last_print=int,
            stop=bint,
            delta=int,
            tasks=int,
            line=str,
            old_line=str)
    cpdef void print_loop(self)
    cpdef void input_loop(self)
    cpdef void _init_actions(self)

