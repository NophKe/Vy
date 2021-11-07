cdef dict _reprs
from cython import locals

@locals(final=str, evaluing=str) 
cpdef str _escape(str text)
