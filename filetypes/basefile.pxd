from .utils cimport RLock
from cython import locals

from threading import Event, Lock
from queue import Queue

cdef class Cancel:
    cdef:
        object lock
        object must_start
        object must_stop
        object all_in_line
        int parties
    
    cdef void notify_stopped(self)
    cdef void notify_working(self)
    cdef void allow_work(self)
    cdef void cancel_work(self)

cdef class DummyLine:
    cdef:
        int _cursor
        str _string
    cpdef void suppr(self)
    cpdef void backspace(self)
    cpdef void insert(self, str text)

cdef class BaseFile:
    cpdef void insert(self, str text)
    cpdef void backspace(self)
    cpdef void suppr(self)

    cdef:
        bint _undo_flag
        public tuple set_comment_string
        #public list update_callbacks
        #public list pre_update_callbacks
        Cancel cancel
        public str _string
        int _cursor

        public RLock _lock
        public tuple _cursor_lin_col # 
        public int _number_of_lin    # but screen uses those vars
        public list _splited_lines   # to only "visit" ephemeral values
        public bint set_number       # TODO should go private
        public bint set_wrap
        public int set_tabsize
        public bint set_expandtabs
        public bint set_autoindent
        
        str _init_text
        tuple _selected      
        str _repr
        list _lines_offsets
        object _lenght
        int _recursion
        str _current_line
        #bint _no_undoing
        list undo_list
        list redo_list
        int _undo_len
        public dict motion_commands
        public object cache_id
        public object path

    cdef void _list_insert(self, str value)
    cdef void _string_insert(self, str value)
    cdef void _list_suppr(self)
    cdef void _string_suppr(self)
    cpdef void insert_newline(self)

#    cpdef _get_range(self,key)          # TODO why is it cpdef ?????
#    cpdef object _get_offset(self, key, default_start=*) # TODO why is it cpdef ?????

    cpdef int find_end_of_line(self)
    cpdef int find_end_of_word(self)
    cpdef int find_end_of_WORD(self)
    cpdef int find_begining_of_line(self)
    cpdef int find_first_non_blank_char_in_line(self)
    cpdef int find_next_non_blank_char(self)
    cpdef int find_normal_k(self)
    @locals(lin=int,
            col=int,
            next_line=int,
            next_lin_offset=int,
            max_offset=int)
    cpdef int find_normal_j(self)
    cpdef int find_normal_l(self)
    cpdef int find_normal_h(self)
    cpdef int find_next_WORD(self)
    cpdef int find_first_char_of_word(self)
    cpdef int find_next_non_delim(self)
    cpdef int find_next_delim(self)
    cpdef int find_previous_delim(self)
#    cdef current_line(self)
#    cdef INNER_WORD(self)
#    cdef inner_word(self)
#    cpdef str getvalue(self)
#    cpdef str read(self, int nchar=*)
#    cpdef int tell(self)
#    cpdef seek(self, int offset=*, flag=*)
    cpdef void move_cursor(self, str offset_str)
    #cpdef void start_undo_record(self)
    #cpdef void stop_undo_record(self)
    #cpdef void set_undo_point(self)
    #cpdef void undo(self)
    #cpdef void redo(self)
    #cpdef void save(self)
    cpdef void save_as(self, object new_path, override=*)
