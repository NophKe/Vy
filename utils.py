from threading import Event, Thread, Lock
from time import sleep

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
        # assert len(self) >= value >= 0
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
    _no_value = object()
    def __init__(self,initial=_no_value, name='undo list'):
        self.data = list()
        self.pointer = 0
        self.skip = False
        self.name = name
        if initial is not self._no_value:
            self.append(initial)
    
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
        # assert not self.skip          
        self.skip = True        
        
    def last_record(self):
        if self.pointer > 0:
            return self.data[self.pointer-1]
        elif self.pointer == 0:
            return self.data[0] 
            # raise only if self.data is truly empty (
        raise IndexError

    def __str__(self):
        return f'( {self.name}: #{self.pointer} /{len(self.data)} )'
        
    def __len__(self):
        return len(self.data)

def eval_effified_str(string):
    # better not work on it now
    return string
    # Is ther really a solution without any edge corner ?
    return eval('f"{' + string + '}"')
    if string[0] == string[-1] == '"':
        return string
    if string[0] == string[-1] == "'":
        return string
    return eval('f"{' + string + '}"')

from concurrent.futures import ThreadPoolExecutor, FIRST_COMPLETED, wait
pool = ThreadPoolExecutor()

def async_update(blocking_call, update):
        future_key_press = pool.submit(blocking_call)         
        new_update = pool.submit(update)
        wait((future_key_press, new_update), return_when=FIRST_COMPLETED)
        if not future_key_press.running():
            new_update.cancel()
#             Thread(target=new_update.result).start()
            return future_key_press.result(), False
        return future_key_press.result(), True

class Cancel:
    def __init__(self):
        self.lock = Lock()
        self.must_stop = Event()
        self.task_done = Event()
        self.task_restarted = Event()
        self.task_started = False

    def notify_working(self):
        while not self.lock.acquire(blocking=False):
            sleep(0)
        self.task_started = True
        self.lock.release()
            
    def notify_task_done(self):
        self.task_done.set()
        self.notify_stopped()
        
    def notify_stopped(self):
        self.must_stop.wait()
        self.task_restarted.set()

    def cancel_work(self):
        self.lock.acquire()
        if self.task_started:
            self.must_stop.set()
            self.task_restarted.wait()
        
            self.task_restarted.clear()
            self.task_done.clear()
            self.must_stop.clear()
            self.task_started = False
            
    def complete_work(self):
        self.task_done.wait()

    def restart_work(self):
        self.cancel_work()
        self.allow_work()

    def allow_work(self):
        self.lock.release()
