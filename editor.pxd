#from vy.interface import Interface
#from vy.console import getch_noblock
#from vy.global_config import DEBUG

#from vy.console cimport getch_noblock
# generator !!!  how to import ????
#from vy.filetypes cimport Open_path

from vy.screen cimport _Screen 
from vy.utils cimport _HistoryList

from cython import final, locals

@final
cdef class _Cache:
    cdef dict _dic
    cdef int _counter
    cdef object _make_key(self, object key)

@final
cdef class NameSpace:
    cdef public object insert
    cdef public object normal
    cdef public object command
    cdef public object visual
    cdef public object motion
#
@final
cdef class _Register:
    cdef dico
    cdef object persistance

@final
cdef class _Editor:
    cdef:
        public dict macros
        public str record_macro
        public list arg_list
        public int arg_list_pointer
        save_in_jump_list(self)
        bint _async_io_flag
        bint _running
        #dict __dict__
        #Interface interface
        object interface
        public _HistoryList jump_list
        list command_list
        list _work_stack
        object command_line
        object _input_queue
        public _Cache cache
        public NameSpace actions
        public object input_thread
        public object print_thread
        public _Register registr
        public _Screen screen
        public str current_mode
        list _macro_keys
    @locals(rv=str,
            key_press=str) 
    cpdef str read_stdin(self)
    cpdef void edit(self, buff)
    cpdef void push_macro(self,str string)
    cpdef void warning(self,str msg)
    cpdef void edit(self, location)
    cpdef void start_async_io(self)
    cpdef void stop_async_io(self)

    #@locals(old_screen=list,
            #to_print=str,
            #index=Py_ssize_t,
            #new_screen=list,
            #filtered=list,
            #last_print=int,
            #stop=bint,
            #tasks=int,
            #line=str,
            #old_line=str)
    cpdef void print_loop(self)
    cpdef void input_loop(self)
    cpdef void _init_actions(self)

