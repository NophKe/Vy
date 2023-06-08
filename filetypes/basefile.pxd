from cython import locals
from vy.utils cimport _HistoryList, Cancel

from threading import Event, Lock
from queue import Queue

cdef class BaseFile:
    cpdef void insert(self,  text) noexcept
    cpdef void backspace(self) noexcept
    cpdef void suppr(self) noexcept

    cdef:
        bint _undo_flag
        public tuple set_comment_string
        Cancel _async_tasks
        public str _string
        int _cursor

        public object _lock
        public tuple _cursor_lin_col # 
        public int _number_of_lin    # but screen uses those vars
        public list _splited_lines   # to only "visit" ephemeral values
        public bint set_number       # TODO should go private
        public bint set_wrap
        public int set_tabsize
        public bint set_expandtabs
        public bint set_autoindent
        int _virtual_col
        
        str _init_text
        tuple _selected      
        str _repr
        list _lines_offsets
        object _lenght
        int _recursion
        str _current_line
        #bint _no_undoing
        public _HistoryList undo_list
        public object cache_id
        public object path

    cdef void _list_insert(self, str value) noexcept
    cdef void _string_insert(self, str value) noexcept
    cdef void _list_suppr(self) noexcept
    cdef void _string_suppr(self) noexcept
    cpdef void insert_newline(self) noexcept

#    cpdef _get_range(self,key)          # TODO why is it cpdef ?????
#    cpdef object _get_offset(self, key, default_start=*) # TODO why is it cpdef ?????

    cpdef int find_end_of_line(self) noexcept
    cpdef int find_end_of_word(self) noexcept
    cpdef int find_end_of_WORD(self) noexcept
    cpdef int find_begining_of_line(self) noexcept
    cpdef int find_first_non_blank_char_in_line(self) noexcept
    cpdef int find_next_non_blank_char(self) noexcept
    cpdef int find_normal_k(self) noexcept
    @locals(lin=int,
            col=int,
            next_line=int,
            next_lin_offset=int,
            max_offset=int)
    cpdef int find_normal_j(self) noexcept
    cpdef int find_normal_l(self) noexcept
    cpdef int find_normal_h(self) noexcept
    cpdef int find_next_WORD(self) noexcept
    cpdef int find_first_char_of_word(self) noexcept
    cpdef int find_next_non_delim(self) noexcept
    cpdef int find_next_delim(self) noexcept
    cpdef int find_previous_delim(self) noexcept
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
    cpdef void save_as(self, object new_path, bint override=*)
