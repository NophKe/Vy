from os import get_terminal_size
from sys import stdout

from vy.filetypes.textfile cimport TextFile

from cython cimport locals, final

@locals(number=str,
        retval=list, 
        cursor_col=int, 
        on_col=Py_ssize_t, 
        esc_flag=bint, 
        cursor_flag=bint,
        char=str,
        nb_of_tabs=int,
        line=str)
cdef list expandtabs_numbered(int tab_size, 
                              int max_col,
                              str text, 
                              int on_lin, 
                              int cursor_lin, 
                              int cursor_col,
                              int num_len,
                              object visual)

@locals(retval=list, 
        cursor_col=int, 
        on_col=int, 
        esc_flag=bint, 
        cursor_flag=bint,
        char=str,
        nb_of_tabs=int,
        line=str)
cdef list expandtabs(int tab_size,
                     int max_col, 
                     str text, 
                     int on_lin, 
                     int cursor_lin, 
                     int cursor_col,
                     int num_len,
                     object visual)

@locals(retval=list, 
        cursor_col=int, 
        on_col=int, 
        esc_flag=bint, 
        char=str,
        line=str)
cdef list expand_quick(int max_col,
                           str text) noexcept


cdef class CompletionBanner:
    cdef:
        int view_start
        int selected
        list completion
        list pretty_completion
        int prefix_len
        object make_func
    #cpdef give_up(self)  noexcept

cdef class Window:
    cdef public tuple _last
    cdef public Window left_panel
    cdef public Window right_panel
    cdef public CompletionBanner minibar_completer
    cdef public TextFile buff
    #cdef public object buff
    cdef Window _focused 
    cdef Window parent
    cdef int shift_to_col
    cdef public int shift_to_lin
    cdef bint _v_split_flag
    cdef int v_split_shift
    cdef list _last_computed
    cdef public tuple shown_lines

    @locals(rv=list,
            max_lin=int,
            to_remove=int,
            default=str,
            on_lin=int,
            line_list=list,
            cursor_line=list,
            true_cursor=int)
    cdef list gen_window(self)

cdef class Screen(Window):
    cdef int _number_of_lin
    cdef int _number_of_col
    cdef str _infobar_right
    cdef str _infobar_left
    cdef tuple _minibar_txt
    cdef list _minibar_completer

#    @locals(rv=list)
#    cpdef tuple get_line_list(self)
#    cpdef void alternative_screen(self)
#    cpdef void original_screen(self)
