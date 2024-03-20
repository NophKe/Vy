from threading import Event as _Event
from threading import Lock
from queue import Queue

class Event(_Event):
    def __bool__(self):
        return self._flag

class DummyLine:
    r"""
    This class provides a simple interface around a line oriented
    buffer. It is meant to be used for simple use-case like implementing
    custom input/scanf function. No optimization, nor locking is made around
    the data.
     
    >>> x = DummyLine()
    >>> x.insert('FOO')
    >>> x.cursor = 0
    >>> x.insert('\n12345')
    >>> x.backspace()
    >>> x.suppr()
    >>> x.string
    '1234FOO'
    """

    ending = ''

    ### TODO: implement other common operations
    ###
    ### - erase word backward
    ### - move cursor to beginning / end of line

    def __init__(self, init_text='', cursor=0):
        assert isinstance(init_text, str)
        assert len(init_text) >= cursor >= 0
        self.string = init_text
        self.cursor = cursor

    @property
    def cursor(self):
        """
        The cursor is a property that returns the position of 
        the cursor as an opaque integer value.
        """
        return self._cursor

    @property
    def string(self):
        """
        string is a property returning the internal buffer value.
        """
        return self._string

    def suppr(self):
        """
        Like the key strike, deletes the character under the cursor.
        """
        string = self.string
        cur = self.cursor
        self.string = string[:cur] + string[cur + 1:]

    def backspace(self):
        """
        Like the key strike, deletes the left character at the cursor.
        """
        if self.cursor > 0:
            self.cursor -= 1
            self.suppr() 

    def insert(self, text):
        """
        Inserts text at the cursor position.
        Cursor will move to end of inserted text.
        """
        string = self.string
        cur = self.cursor
        self.string = f'{string[:cur]}{text}{string[cur:]}'
        self.cursor += len(text)
    
    @string.setter
    def string(self, value):
        # to make assert statements happy, 
        # allways update STRING _before_ CURSOR
        assert value.endswith(self.ending)
        self._string = value

    @cursor.setter
    def cursor(self, value):
        assert len(self) >= value >= 0
        self._cursor = value

    def __len__(self):
        return len(self._string) - len(self.ending)

class TextLine(DummyLine):
    """
    TODO -- This class should soon be the return value
           of the different BaseFile properties.
    """
    ending = '\n'

class _HistoryList:
    def __init__(self):
        self.data = list()
        self.pointer = 0
        self.skip = False
    
    def append(self, value):
        if self.skip:
            self.skip = False
        else:
            self.data.insert(self.pointer, value)
            self.pointer += 1
    
    def pop(self):
        if self.pointer > 0:
            self.pointer -= 1
            return self.data[self.pointer]
        raise IndexError
    
    def push(self):
        if self.pointer == len(self.data):
            raise IndexError
        self.pointer += 1
        return self.data[self.pointer-1]
    
    def skip_next(self):
        assert not self.skip        
        self.skip = True        
        
    def last_record(self):
        if self.pointer > 0:
            return self.data[self.pointer-1]
        elif self.pointer == 0:
            return self.data[0] 
            # raise only if self.data is truly empty (
        raise IndexError

    def __str__(self):
        return '\n'.join( repr(value) + ' <-- pointer' if idx == self.pointer 
                          else repr(value) for idx, value in enumerate(self.data) )

class Cancel:
    def __init__(self):
        self.lock = Lock()
        self.must_stop = Event()
        self.task_done = Event()
        self.restart = Queue(1)
        self.working = False
        self.cancelled = False

    def notify_working(self):
        while self.must_stop.wait(0):
            pass
        with self.lock:
            self.working = True
            
    def notify_task_done(self):
        self.task_done.set()
        self.notify_stopped()
        
    def notify_stopped(self):
        self.must_stop.wait()
        self.restart.put(None)
        self.restart.join()

    def cancel_work(self):
        if not self.cancelled:
            self.lock.acquire()
            self.must_stop.set()
            if self.working:
                self.restart.get()
            self.task_done.clear()
            self.cancelled = True

    def complete_work(self):
        self.task_done.wait()

    def restart_work(self):
        self.cancel_work()
        self.allow_work()

    def allow_work(self):
        self.cancelled = False
        self.must_stop.clear()
        if self.working:
            self.restart.task_done()
            self.working = False
        self.lock.release()

from _thread import allocate_lock
from threading import current_thread

class RwLock:
    def __init__(self):
        self.read_lock = allocate_lock()
        self.write_lock = allocate_lock()
        self.members = 0

    def lock_reading(self):
        with self.read_lock:
            if self.members == 0:
                self.write_lock.acquire()
            self.members += 1
    
    def unlock_reading(self):
        with self.read_lock:
            self.members -= 1
            if self.members == 0:
                self.write_lock.release()

    def lock_writing(self):
        self.write_lock.acquire()
        assert not self.members

    def unlock_writing(self):
        assert not self.members
        self.write_lock.release()

class AtomicCounter:
    def __init__(self, start=0):
        self.lock = allocate_lock()
        self.value = start
        
    def increment(self):
        with self.lock:
            self.value += 1

    def decrement(self):
        with self.lock:
            self.value -= 1

    def __bool__(self):
        return self.value != 0

class Canceller:
    def __init__(self):
        self.lock = RwLock()
        self.must_stop = AtomicCounter()
        self.waiters = []
        self.owner = None

    def notify_working(self):
        self.lock.lock_reading()
        
    def notify_stopped(self):
        wait_event = allocate_lock()
        wait_event.acquire()
        self.waiters.append(wait_event)
        self.lock.unlock_reading()
        wait_event.acquire()
        wait_event.release()

    def cancel_work(self):
        if self.owner != current_thread:
            self.lock.lock_writing()            
            self.owner = current_thread()
        self.must_stop.increment()

    def restart_work(self):
        self.cancel_work()
        self.allow_work()

    def allow_work(self):
        self.must_stop.decrement()
        if not self.must_stop:
            for waiter in self.waiters:
                waiter.release()
            self.waiters.clear()
        self.lock.unlock_writing()

#Cancel = Canceller
