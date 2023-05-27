from cython import final

@final
cdef class Cancel:
    cdef:
        object lock
        object must_start
        object must_stop
        object all_in_line
        int parties
    
    cpdef void notify_stopped(self) noexcept
    cpdef void notify_working(self) noexcept
    cpdef void allow_work(self) noexcept
    cpdef void cancel_work(self) noexcept

cdef class DummyLine:
    cdef:
        int _cursor
        str _string
    cpdef void suppr(self) noexcept
    cpdef void backspace(self) noexcept
    cpdef void insert(self, str text) noexcept

@final
cdef class _HistoryList:
    cdef:    
        list data
        int pointer
        bint skip
    cpdef append(self, value) noexcept
    cdef pop(self)
    cpdef push(self)
    cpdef skip_next(self) noexcept
    cpdef last_record(self)
