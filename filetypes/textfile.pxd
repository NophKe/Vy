from vy.filetypes.basefile cimport BaseFile

cdef class TextFile(BaseFile):
    cdef:
        public object PROC
        public object _lexed_away
        public object _lexer_request
    cpdef tuple get_lexed_line(self, int index)
    cpdef tuple PROC_lexed_string(self, send_queue, recv_queue)
