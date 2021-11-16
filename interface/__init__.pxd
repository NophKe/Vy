from vy.editor cimport _Editor

cdef class Interface:
    cdef str last
    cdef _Editor inst
    cdef dict mode_dict
