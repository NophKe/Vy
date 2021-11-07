from vy.keys cimport _escape

cdef class command:
    cdef:
        str c_header 
        str n_header 
        str v_header 
        str i_header 
    cdef str category 
    cdef update_func(self, str alias, func)
