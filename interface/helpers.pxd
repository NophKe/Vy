from vy.screen cimport Screen
from vy.editor cimport _Editor
from vy.filetypes.basefile cimport DummyLine
#cdef class CommandCompleter:
#        cdef public object histfile
#        cdef public object _old_complete
#        cpdef str completer(self, str txt, int state)
#
cpdef bint one_inside_dict_starts_with(dict dictio, str pattern)

cdef class Completer:
    cdef:
        list history
        list completion
        dict dictionary
        int max_selected
        object histfile
        object reader
        str state
        int selected
        list last_print
        str prompt
        Screen screen
        _Editor editor
        DummyLine buffer

    #cpdef list get_history(self)
    #cpdef list get_complete(self)
    cdef void complete(self)
    cdef void give_up(self)
    cdef void move_left(self)
    cdef void move_right(self)
    cdef void move_cursor_up(self)
    cdef void move_cursor_down(self)
    cdef str select_item(self)
    #cdef list get_complete(self)
    #cdef list get_history(self)
