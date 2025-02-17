from cython import final

from threading import Event as _Event
from threading import Lock
from queue import Queue

@final
cdef class Cancel:
    cdef:
        object lock
        object task_restarted
        
        public object must_stop
        public object task_started

    cpdef void notify_stopped(self) noexcept
    cpdef void notify_working(self) noexcept
    cpdef void allow_work(self) noexcept
    cpdef void cancel_work(self) noexcept
    cpdef void restart_work(self) noexcept

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
        str name
    cpdef append(self, value) noexcept
    cdef pop(self)
    cpdef push(self)
    cpdef skip_next(self) noexcept
    cpdef last_record(self)
