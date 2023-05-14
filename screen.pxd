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
                           str text)


cdef class CompletionBanner:
    cdef:
        int view_start
        int max_selected 
        int selected
        public list completion
        list pretty_completion
        int prefix_len
        object check_func 
        object make_func
        bint _active

        generate(self)
        _update(self)

    cpdef set_callbacks(self, object make_func, object check_func)
    cpdef give_up(self)

    cpdef move_cursor_up(self)
    cpdef move_cursor_down(self)
    cpdef select_item(self)

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

    @locals(rv=list,
            max_lin=int,
            to_remove=int,
            default=str,
            on_lin=int,
            line_list=list,
            cursor_line=list,
            true_cursor=int)
    cdef list gen_window(self)

@final
cdef class Screen(Window):
    cdef int _number_of_lin
    cdef int _number_of_col
    cdef str _infobar_right
    cdef str _infobar_left
    cdef list _minibar_txt
    cdef list _minibar_completer

    @locals(rv=list)
    cpdef tuple get_line_list(self)
    cpdef void alternative_screen(self)
    cpdef void original_screen(self)
