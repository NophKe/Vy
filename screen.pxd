from vy.filetypes.textfile cimport TextFile
import cython

cpdef str get_prefix(str token)
cdef str _resolve_prefix(str color_string)
cdef int get_rows_needed(int number)

@cython.locals(number=str,
                retval=list, 
                cursor_col=int, 
                on_col=int, 
                esc_flag=bint, 
                cursor_flag=bint)
cdef list expandtabs_numbered(int tab_size, int max_col, str text, int on_lin, int cursor_lin, int cursor_col)

@cython.locals(number=str,
                retval=list, 
                cursor_col=int, 
                on_col=int, 
                esc_flag=bint, 
                cursor_flag=bint)
cdef list expandtabs(int tab_size, int max_col, str text, int on_lin, int cursor_lin, int cursor_col)

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
    cdef int _true_lines

cdef class Screen(Window):
    cdef int _minibar_flag
    cdef list _old_screen
    cdef object _old_term_size
