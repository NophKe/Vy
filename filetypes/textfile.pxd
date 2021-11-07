cdef:
    dict colorscheme
    dict codes
    dict formatters
    str SET_DEF
    str DELIMS

cdef class TextFile:
    cdef:
        #dict __dict__
        bint _no_undoing
        dict color_prefix
        #list _post_lexed_lines
        list redo_list
        list _splited_lines
        list undo_list
        public list _lexed_lines   ## Public !!!
        list _lines_offsets
        public object PROC
        #public object manager
        public object _lexed_away
        public object _lexer_request
        public bint set_number
        public bint set_wrap
        public dict motion_commands
        public int cursor
        public int set_tabsize
        public object cache_id
        object lexer
        public object path
        public object _selected_end1
        public object _selected_end2
        public str _string

    cdef _get_range(self,key)
    cdef int _get_offset(self, key)

    cdef int find_end_of_line(self)
    cdef int find_end_of_word(self)
    cdef int find_end_of_WORD(self)
    cdef int find_begining_of_line(self)
    cdef int find_first_non_blank_char_in_line(self)
    cdef int find_next_non_blank_char(self)
    cdef int find_normal_k(self)
    cdef int find_normal_j(self)
    cdef int find_normal_l(self)
    cdef int find_normal_h(self)
    cdef int find_next_WORD(self)
    cdef int find_next_word(self)
    cdef int find_first_char_of_word(self)
    cdef int find_normal_b(self)
    cdef int find_next_non_delim(self)
    cdef int find_next_delim(self)
    cdef int find_previous_delim(self)
    cpdef tuple get_lexed_line(self, int index)
    cpdef tuple PROC_lexed_string(self, send_queue, recv_queue)
#    cdef current_line(self)
#    cdef INNER_WORD(self)
#    cdef inner_word(self)
    cpdef void suppr(self)
    cpdef void backspace(self)
    cpdef void insert(self, str text)
    cpdef str getvalue(self)
    cpdef str read(self, nchar=*)
    cpdef int tell(self)
    cpdef seek(self, int offset=*, flag=*)
    cpdef void move_cursor(self, offset_str)
    cpdef void start_undo_record(self)
    cpdef void stop_undo_record(self)
    cpdef void set_undo_point(self)
    cpdef void undo(self)
    cpdef void redo(self)
    cpdef void save(self)
    cpdef void save_as(self, new_path=*, override=*)
