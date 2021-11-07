from vy.editor cimport Editor

cdef class Interface:
    cdef str last
    cdef Editor inst
    cdef dict mode_dict
