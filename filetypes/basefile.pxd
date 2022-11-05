from cython import locals
from vy cimport keys as k

cdef class DummyLine:
    cdef:
        int _cursor
        str _string
    cpdef void suppr(self)
    cpdef void backspace(self)
    cpdef void insert(self, str text)

cdef class TextLine(DummyLine):
    pass

cdef class BaseFile:
    cpdef void suppr(self)
    cpdef void backspace(self)
    cpdef void insert(self, str text)

    cdef:
        str _string
        int _cursor

        public tuple _cursor_lin_col # 
        public int _number_of_lin    # but screen uses those vars
        public list _splited_lines   # to only "visit" ephemeral values
        public bint set_number       # TODO should go private
        public bint set_wrap
        public int set_tabsize

        str _repr
        list update_callbacks
        list pre_update_callbacks
        list _lines_offsets
        object _lenght
        int _recursion
        str _current_line
        object _lock
        #bint _no_undoing
        list undo_list
        list redo_list
        public dict motion_commands
        public object cache_id
        public object path

    cdef void _list_insert(self, str value)
    cdef void _string_insert(self, str value)
    cdef void _list_suppr(self)
    cdef void _string_suppr(self)
    cpdef void insert_newline(self)

    cpdef _get_range(self,key)          # TODO why is it cpdef ?????
    cpdef object _get_offset(self, key) # TODO why is it cpdef ?????

    cdef int find_end_of_line(self)
    cdef int find_end_of_word(self)
    cdef int find_end_of_WORD(self)
    cdef int find_begining_of_line(self)
    cdef int find_first_non_blank_char_in_line(self)
    cdef int find_next_non_blank_char(self)
    cdef int find_normal_k(self)
    @locals(lin=int,
            col=int,
            next_line=int,
            next_lin_offset=int,
            max_offset=int)
    cdef int find_normal_j(self)
    cdef int find_normal_l(self)
    cdef int find_normal_h(self)
    cdef int find_next_WORD(self)
    cdef int find_first_char_of_word(self)
    cdef int find_normal_b(self)
    cdef int find_next_non_delim(self)
    cdef int find_next_delim(self)
    cdef int find_previous_delim(self)
#    cdef current_line(self)
#    cdef INNER_WORD(self)
#    cdef inner_word(self)
    cpdef str getvalue(self)
    cpdef str read(self, int nchar=*)
    cpdef int tell(self)
    cpdef seek(self, int offset=*, flag=*)
    cpdef void move_cursor(self, str offset_str)
    #cpdef void start_undo_record(self)
    #cpdef void stop_undo_record(self)
    cpdef void set_undo_point(self)
    cpdef void undo(self)
    cpdef void redo(self)
    cpdef void save(self)
    cpdef void save_as(self, new_path=*, override=*)
