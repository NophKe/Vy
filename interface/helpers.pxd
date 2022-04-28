#cdef class CommandCompleter:
#        cdef public object histfile
#        cdef public object _old_complete
#        cpdef str completer(self, str txt, int state)
#
cpdef bint one_inside_dict_starts_with(dict dictio, str pattern)
