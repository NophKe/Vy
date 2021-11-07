from cython import locals

cdef class stdin_no_echo:
    cdef list mode
#
cdef class stdin_no_echo_nl:
    cdef dict __dict__

@locals(mode=list)
cdef setnoecho(fd, when=*)

@locals(mode=list)
cdef setnonblocking(fd, when=*)

@locals(rv=str, esc_seq=str)
cpdef str get_a_key()

@locals(rv=str, esc_seq=str)
cdef stdout_no_cr()
