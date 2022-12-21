from cython cimport locals, final

cdef:
   int IFLAG
   int OFLAG
   int CFLAG
   int LFLAG
   int ISPEED
   int OSPEED
   int CC

#@locals(mode=list)
#cdef setnoecho(fd, when=*)

@locals(mode=list)
cdef setraw(fd, when=*)

@locals(mode=list)
cdef setnonblocking(fd, when=*)

@locals(rv=str, esc_seq=str)
cdef str getch()

