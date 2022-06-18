from vy.filetypes.textfile cimport TextFile
from cython cimport locals, final

cdef int get_rows_needed(int number)

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
                              int cursor_col)

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
                     int cursor_col)

cdef class Window:
    cdef public Window left_panel
    cdef public Window right_panel
    cdef public TextFile buff
    cdef Window _focused 
    cdef Window parent
    cdef int shift_to_col
    cdef public int shift_to_lin
    cdef bint _v_split_flag
    cdef int v_split_shift
    cdef list gen_window(self, bint flash_screen)

@final
cdef class Screen(Window):
    cdef int _number_of_lin
    cdef int _number_of_col
    cdef str _infobar_txt
    cdef list _minibar_txt
    cdef list _minibar_completer

    @locals(rv=list)
    cpdef list get_line_list(self, bint flash_screen=*)
    cdef void alternative_screen(self)
    cdef void original_screen(self)
    cdef void recenter(self, Py_ssize_t discard_lines=*, bint flash_screen=*)
    #cdef void minibar_completer(self, str *lines)
    #cdef void minibar(self, str *lines)
    #cpdef void infobar(self, str right=*, str left=*)
    # TODO look for correct syntax to declare *args (variable lenght)...

