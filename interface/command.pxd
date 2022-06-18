# For typing definitions
from vy cimport keys as k
from vy.editor cimport _Editor
from vy.screen cimport Screen
from vy.filetypes.basefile cimport InputBuffer
from vy.interface.helpers cimport one_inside_dict_starts_with

# Cython declaration utils
from cython cimport final, locals

cdef object Path

# Module content definition
@final
cdef class Completer:
    cdef:
        dict dictionary
        int max_selected
        object histfile
        str state
        int selected
        list last_print
        str prompt
        Screen screen
        _Editor editor
        InputBuffer buffer

    cdef str get_history(self)
    cdef list get_complete(self)
    cdef void complete(self)
    cdef void give_up(self)
    cdef void move_left(self)
    cdef void move_right(self)
    cdef void move_cursor_up(self)
    cdef void move_cursor_down(self)
    cdef str select_item(self)

cdef Completer readline 

@locals(ARG=str,
        PART=str,
        REG=str,
        cmd=str,
        user_input=str,
        action=object)
cpdef str loop(_Editor self)
