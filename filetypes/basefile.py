"""
BaseFile is... ( well... ) the basis for what is usually called a
«buffer» in the in the Vi-like editors jargon.

It mixes the classical expected features of a mutable string with some 
traditionnal concepts of vim buffers, like motions.

>>> file = BaseFile(init_text='Hello World\n 42\n' , cursor=0)

>>> file.move_cursor('w')            # moves to next word ( regex \b )
>>> assert file.cursor == 6
>>> # assert file[:11] == file[':$']  # vim style buffer slice ( regex ^.*$ ) 

All of its public methods are atomic (using an internal threading.RLock 
object). If you need to modify the buffer, you can acquire its internal 
lock by using it as a context manager.

>>> with file:
...        assert file.number_of_lin == len(file.splited_lines) \
...        == len(file.lines_offsets)

To modify the content of the buffer: use one of its three setters 
properties. (string,  current_line and cursor). Any modifications of one
of those properties will immediatly invalidate any other property that 
depend on it. 
Properties being lazily evaluated, a few «fast paths» are provided
to speed up common operations upon the internal data structure.
Do not rely on them!  Being lazily computed, a lot of the
properties assert themselves  towards each other.  Some
assertions are clearly redundant but will be maintained for
correctness.  Moreover speed on that matter may strongly depend
on you python implementation.

>>> file.insert_newline()
>>> file.insert('\n')

By definition, one line should allways end by a newline.  Also one
empty line is represented by EMPTY STRING + NEWLINE.  The newline
character has no special treatment anywhere in the file, you can
delete them and insert new ones any time, but the last newline
character that ends the buffer cannot be deleted.

>>> file.backspace()
>>> file.suppr()

A Buffer may also be used as a replacement for a file object.

One may also consider a buffer as a mutable sequence suitable as a
remplacement of the immutable string.

>>> file[0:6]
'Hello '
>>> file[0:8] = '@ too big to fit in there'
>>> file[0] = 'never'
>>> file[:29]
'never too big to fit in there'

NOTE: the word «offset» will be used to speak about characters and their
     positions, whereas «index» will be used for line numbers.
"""

from vy.lsp_client import open_lsp_channel
from vy.utils import _HistoryList, DummyLine, Cancel

from threading import RLock
from sys import intern
from re import split as _split
from functools import lru_cache

DELIMS = '+=#/?*<> ,;:/!%.{}()[]():\n\t\"\''

def make_word_set(string):
    """
    >>> raise Error
    """
    return set(_split(r'[{}\. :,()\[\]]|$|\t', string))

class BaseFile:
    ANY_BUFFER_WORD_SET = set()

    modifiable = True
    actions = {}
    ending = '\n'   
    
    set_tabsize = 4
    set_wrap = True
    set_autoindent = False
    set_expandtabs = False
    set_number = True

    _lsp_server = None
    _lsp_lang_id = None

    def __init__(self, /, cursor=0, init_text='', path=None):
        # start of private
        self._virtual_col = 0
        self._selected = None
        self._repr = '' #TODO delete me ?
        self._undo_flag = True
        self._states = [init_text]
        self._number_of_lin = 0
        self._cursor_lin_col = ()
        self._current_line = ''
        self._lines_offsets = list()
        self._async_tasks = Cancel()
        self._lock = RLock()
        self._recursion = 0

        self.path = path # must be first
        self.undo_list = _HistoryList(initial=(init_text, (0,0)), name='undo list')
        self.word_set = set()

        # give the buffer its initial content
        self._lenght = len(init_text)
        self._cursor = cursor
        self._string = init_text
        _splited_lines = init_text.splitlines(True)
        self._splited_lines = _splited_lines

        # trigger properties computation
        self.cursor_lin_col
        self.number_of_lin

        if self._lsp_server:
            self._lsp_server = open_lsp_channel(self._lsp_server, self)
        if self._lsp_server:
            self._lsp_server.text_document_did_open(self._path_as_uri, self._lsp_lang_id, 1, self.string) 
            
        for line in _splited_lines:
            for w in make_word_set(line):
                if w not in self.word_set:
                    self.ANY_BUFFER_WORD_SET.add(w)
                self.word_set.add(w)


    def _notify_lsp_content_change(self):
        """ Notify the LSP server of file content and cursor changes. """
        if self._lsp_server:
            self._lsp_server.text_document_did_change(self._path_as_uri, 1, [{ "text": self.string }]) 
           
    
    def auto_complete(self):
#        with self._lock:
            word = self.string[self.find_previous_delim():self.cursor+1].strip()
            prefix_len = len(word)
            if prefix_len:
                rv = [item for item in self.word_set if item.startswith(word)]
                if not rv or (len(rv) == 1 and rv[0] == word):
                    rv = [item for item in self.ANY_BUFFER_WORD_SET if item.startswith(word)]
            else:
                rv = []
                
            return rv, prefix_len


    def __enter__(self):
        if self.modifiable:
            self._lock.acquire()
            self._recursion += 1
            if self._recursion == 1:
                self._async_tasks.cancel_work()
            else:
                self._lock.release()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.modifiable:
            self._recursion -=    1
            if self._recursion == 0:
#                self._test_all_assertions()
                self._async_tasks.allow_work()
                if self._lsp_server:
                    self._notify_lsp_content_change()
                self._lock.release()

    @property
    def string(self):
        """
        string is a property returning the internal buffer.  Modifying
        its value triggers the registered callbacks and invalidates the
        properties that depend on it.
        
        As there is no way of knowing in advance what the new value will
        be, avoid modifying it directly.  This will invalidate most
        computation allready done.
        """
        with self._lock:
            if not self._string:
                self._string = ''.join(self._splited_lines)
            return self._string

    @property
    def cursor_lin_col(self):
        """
        A tupple representing the actual cursor (line, collumn),
        lines are 0 based indexed, and cols are 1-based.
        
        This property should be the main api to modify the cursor.
        """
        with self._lock:
            if not self._cursor_lin_col:
                lin, off = self.current_line_off
                try:
                    col = self.cursor - off + 1
                except TypeError:
                    breakpoint()
                self._cursor_lin_col = (lin, col)
            return self._cursor_lin_col

    @cursor_lin_col.setter
    def cursor_lin_col(self, pair_value):
        with self._lock:
            old_lin, old_col = self.cursor_lin_col
            new_lin, new_col = pair_value
            nb_lin = self.number_of_lin

            new_lin = min(nb_lin-1, max(0, new_lin))
            self._current_line = self.splited_lines[new_lin]
            
            if not self._virtual_col:
                self._virtual_col = old_col
            else:
                if not new_col: 
                    new_col = self._virtual_col
                else:
                    self._virtual_col = new_col
            
            new_col = max(1, min(new_col, len(self._current_line)))
            self._cursor = self.lines_offsets[new_lin] + new_col - 1
            self._cursor_lin_col = (new_lin, new_col)

    @property
    def current_line_off(self):
        """
        A tupple (current_line_idx, current_line_off),
        lines are 0 based indexed, and cols are 1-based.
        """
        with self._lock:
            if self._lines_offsets and self._cursor_lin_col:
                lin, _ = self._cursor_lin_col
                return lin, self._lines_offsets[lin]

            cursor = self.cursor
            lin = offset = 0
            for lin, offset in enumerate(self.lines_offsets):
                if offset == cursor:
                    return lin, offset
                if offset > self.cursor:
                    return lin - 1, self._lines_offsets[lin - 1 ]
            else:
                return lin, offset

    @property
    def current_line_idx(self):
        """
        Index of current line. (The one the cursor is on)
        """
        with self._lock:
            lin, _ = self.cursor_lin_col
            return lin

    @property
    def lines_offsets(self):
        """
        This is the list of the offsets of all the beginning of lines,
        first line starts at 0
        """
        with self._lock:
            if not self._lines_offsets:
                final = list()
                offset = 0
                for line in self.splited_lines:
                    final.append(offset)
                    offset += len(line)
                self._lines_offsets = final
            return self._lines_offsets

    @property
    def splited_lines(self):
        r"""
        This is the list of the lines contained in the buffer, each should 
        have a trailing newline.
        -
        >>> assert all(
        ... sum(len(lines) for lines in x.splited_lines[:index])
        ... == 
        ... x.lines_offsets[index] for index in range(0, x.number_of_lin)  )
        >>>
        """
        with self._lock:
            if not self._splited_lines:
                self._splited_lines = self._string.splitlines(True)
            return self._splited_lines

    @property
    def number_of_lin(self):
        """
        Number of lines in the buffer.
        """
        with self._lock:
            if not self._number_of_lin:
                self._number_of_lin = len(self.splited_lines)
            return self._number_of_lin


    def generate_properties(self):
        from itertools import accumulate
#        self._lines_offsets = list(accumulate(map(len, splited_lines), sum))
        return list(accumulate(map(len, self.splited_lines), initial=0))
                
    def suppr(self):
        r"""
        Like the key strike, deletes the character under the cursor.

        >>> x = BaseFile(init_text='0123\n5678', cursor=0)
        >>> for _ in range(12):
        ...        x.suppr()
        >>> x.string
        '\n'
        """
        with self:
            if self._splited_lines:
                self._list_suppr()
            else:
                self._string_suppr()

    def _list_suppr(self):
        lin, col = self.cursor_lin_col
        cur_lin = self.current_line
        col -= 1
        if cur_lin[col]  == '\n':
            self.join_line_with_next()
#            self._string_suppr()
            return
        self._current_line  = f'{cur_lin[:col]}{cur_lin[col + 1:]}'
        self._splited_lines[lin] = self._current_line
        self._string = ''
        self._lenght -= 1
        self._lines_offsets.clear()

    def _string_suppr(self):
        string = self.string
        cur = self.cursor
        self.string  = string[:cur] + string[cur + 1:]

    def backspace(self):
        """
        Like the key strike, deletes the left character at the cursor.
        """
        with self:
            if self.cursor > 0:
                self.cursor -= 1
                self.suppr() 

    def insert(self, value):
        """
        Inserts value at the cursor position.
        Cursor will move to end of inserted text value.
        """
        if self.modifiable:
            with self:
                if value == '\n':
                    self.insert_newline()
                elif '\n' not in value:
                    self._list_insert(value)
                else:
                    self._string_insert(value)

    def _string_insert(self, value):
        string = self.string
        cur = self.cursor
        self._string = f'{string[:cur]}{value}{string[cur:]}'
        self._cursor += len(value)
        self._number_of_lin = self._string.count('\n')
        self._lines_offsets.clear()
        self._lenght = len(self._string)
        self._current_line = ''
        self._cursor_lin_col = ()
        self._splited_lines.clear()

    def _list_insert(self, value):
        lin, col = self.cursor_lin_col
        string = self.current_line
        self._string = ''
        cur = col - 1
        self._cursor += len(value)
        self._cursor_lin_col = (lin, col + len(value))
        self._current_line = f'{string[:cur]}{value}{string[cur:]}'
        self._splited_lines[lin] = self._current_line
        self._lines_offsets.clear()
        self._lenght += len(value)

    def start_selection(self):
        self._selected = self.cursor_lin_col
    
    def stop_selection(self):
        self._selected = ()

    @property
    def selected_offsets(self):
        if self._selected:
            lin, col = self._selected
            a = self.lines_offsets[lin] + col - 1
            b = self.cursor
            return slice(min(a, b), max(a, b))
        return slice(self.cursor, self.cursor + 1)

    @property
    def selected_lin_col(self):
        if not self._selected:
            return None
        a_lin, a_col = self._selected
        b_lin, b_col = self.cursor_lin_col
        if a_lin < b_lin:
            return (a_lin, a_col), (b_lin, b_col)
        elif a_lin == b_lin:
            if a_col < b_col:
                return (a_lin, a_col), (b_lin, b_col)
            return (a_lin, b_col), (b_lin, a_col)
        return (b_lin, b_col), (a_lin, a_col)
            
    @property
    def selected_lines_off(self):
        a = self.lines_offsets[self.current_line_idx]
        try:
            b = self.lines_offsets[self._selected[0]+1]
        except IndexError:
            b = len(self)
        return slice(min(a, b), max(a, b))

    @property
    def selected_lines(self):
        if self._selected:
            with self._lock:
                actual_lin = self.current_line_idx
                other_lin = self._selected[0]
            return range(min(actual_lin, other_lin), max(actual_lin, other_lin)+1)
        return range(0)

    def __len__(self):
        with self._lock:
            return self._lenght
    

    def join_line_with_next(self):
        with self:
            line_idx = self.current_line_idx
            next_line_idx = line_idx + 1
            if next_line_idx != self.number_of_lin:
                # nothing to do on last line
                self._current_line = self.current_line.removesuffix('\n') \
                                     + self.splited_lines[next_line_idx]
                self._splited_lines[line_idx] = self._current_line
                self._splited_lines.pop(next_line_idx)
                self._lines_offsets.clear()
                self._lenght -=1
                self._number_of_lin -= 1
                self._string = ''

    def insert_newline(self):
        """
        This function inserts a newline using a «fast path».

        It does so by checking what is allready being computed, and
        delaying expensive computations.
        """
        if self.modifiable:
            with self:
                if self._splited_lines:
                    self._lenght += 1
                    self._number_of_lin += 1
                    lin, col = self.cursor_lin_col

                    top = (self._splited_lines[lin])[:col-1] + '\n'
                    bottom = (self._splited_lines[lin])[col-1:]
                    self._splited_lines.insert(lin, top)
                    self._splited_lines[lin+1] = bottom
                    self._current_line = bottom
                    self._string = ''
                    self._cursor_lin_col = (lin+1, 1)
                    self._cursor += 1
                    self._lines_offsets.clear()
    
                else:
                    self._string_insert('\n')
    
    @property
    def current_line(self):
        with self._lock:
            if not self._current_line:
                self._current_line = self.splited_lines[self.current_line_idx]
            return self._current_line

    @current_line.setter
    def current_line(self, value):
        if self.modifiable:
            with self:
                assert value.endswith('\n') and '\n' not in value[:-1], f'{repr(value) = }'
                lin = self.current_line_idx
                old_val = self._splited_lines[lin]
                self._lenght -= len(old_val) - len(value)

                self._splited_lines[lin] = value
                self._string = ''
                self._current_line = value
                self._lines_offsets.clear()
                self._notify_lsp_content_change()
    
    @property
    def cursor(self):
        """
        The cursor is a property that returns the position of the cursor as an
        opaque integer value.
        """
        with self._lock:
            return self._cursor

    @cursor.setter
    def cursor(self, value):
        assert 0 <= value < self._lenght
        with self._lock:
            self._current_line = ''
            self._cursor_lin_col = ()
            self._cursor = value
            self.cursor_lin_col

    @string.setter
    def string(self, value):
        if self.modifiable:
            with self:
                self._current_line = ''
                self._splited_lines.clear()
                self._lines_offsets.clear()
                
                if not value.endswith(self.ending):
                    value += self.ending
                    
                self._string = value
                self._number_of_lin = value.count('\n')
                self._lenght = len(self._string)
                self._cursor_lin_col = ()
                self._notify_lsp_content_change()

    def set_undo_point(self):
        try:
            last_saved = self.undo_list.last_record()[0]
        except IndexError:
            last_saved = ''
            
        with self._lock:
            value = self.string
            if last_saved != value:	
                position = self.cursor_lin_col
                self.undo_list.append((value, position))

    def undo(self):
        with self:
#            self.undo_list.skip_next()            # first
            txt, pos = self.undo_list.pop()    # second
            if isinstance(txt, str):
                self.string = txt
            elif isinstance(txt, list):
                self._splited_lines = txt
            else:
                raise TypeError
                
            if isinstance(pos, tuple):
                self.cursor_lin_col = pos
            elif isinstance(pos, int):
                self.cursor = pos
            else:
                raise TypeError
            
    def redo(self):
        with self:
            txt, pos = self.undo_list.push() # raises
            self.string = txt
            self.cursor_lin_col = pos
        
    def find_end_of_line(self):
        r"""
        >>> x=BaseFile(init_text="0____5\n___")
        >>> x.cursor = 0
        >>> x.find_end_of_line()
        6
        """
        offset = self.string.find('\n', self.cursor)
        if offset == -1:
            return len(self)
        return offset

    def find_end_of_word(self):
        r"""
        This should correspond to normal mode 'e' motion.
        #>>> x=BaseFile(init_text="foo,bar;baz.foo,bar/baz!foo%bar")
        #>>> # breaks       ||  ||  ||  ||  ||  ||  ||  |             
        #>>> # breaks       2|  6| 10| 14| 18| 22| 26| 30             
        #>>> # breaks        3    7  11  15  19  23  27                 
        """
        global DELIMS
        places = set()
        if (start := self.cursor + 2) > len(self):
            return self.cursor
        for char in DELIMS:
            loc = self.string[start:].find(char)
            if loc > -1:
                loc += self.cursor
                places.add(loc+1)
        if places:
            return min(places)
        return self.cursor

    def find_end_of_WORD(self):
        start = self.cursor
        try:
            while self.string[start].isspace():
                start += 1

            start = self.cursor + 2
            if start > len(self):
                return self.cursor
            sp_offset = self.string.find(' ', start)
            nl_offset = self.string.find('\n', start)
            offset = min(sp_offset, nl_offset)
            if offset == -1:
                return len(self)
            return start + offset
        except IndexError:
            return self.cursor

    def find_begining_of_line(self):
        with self._lock:
            return self.lines_offsets[self.current_line_idx]

    def find_first_non_blank_char_in_line(self):
        pos = self.lines_offsets[self.current_line_idx]
        stop = pos + len(self.current_line) - 1
        string = self.string
        while string[pos].isspace() and pos < stop:
            pos += 1
        return pos

    def find_next_non_blank_char(self):
        pos = self.cursor
        string = self.string
        while string[pos].isspace() and pos < len(string):
            pos += 1
        return pos

    def find_normal_k(self):
        with self._lock:
            lin, col = self.cursor_lin_col
            if not lin:
                return 0
            current_line_start = self.lines_offsets[lin]
            previous_line = self._lines_offsets[lin-1]

            if previous_line + col < current_line_start:
                return previous_line + col - 1
            else:
                return current_line_start - 1

    def find_normal_j(self):
        with self._lock:
            lin, col = self.cursor_lin_col
            next_line = lin + 1
            if next_line > self.number_of_lin:
                return self.cursor

            try:
                next_lin_offset = self.lines_offsets[next_line]
            except IndexError:
                return self.cursor

            max_offset = next_lin_offset + len(self.splited_lines[next_line])
            if next_lin_offset + col > max_offset:
                return max_offset
            return next_lin_offset + col - 1

    def find_next_WORD(self):
#TODO CHeck for end of file
        cursor = self.cursor +1
        try:
            if not self.string[cursor].isspace():
                while not self.string[cursor].isspace():
                    cursor += 1
            while self.string[cursor].isspace():
                cursor += 1
        except IndexError:
            pass
        finally:
            return cursor

    def find_first_char_of_word(self):
        if self.cursor == 0:
            return 0
        elif self.string[self.cursor - 1].isspace():
            return self.cursor
        else:
            return self.string[:self.cursor].rfind(' ') + 1

    def find_normal_B(self):
        lin, col = self.cursor_lin_col
        cur_lin = self.current_line
        befor_cur = cur_lin[:col-1]
        pos = befor_cur.rfind(' ')
        _, off = self.current_line_off
        if pos > 0:
            return off + pos
        return off

    def find_next_non_delim(self):
        global DELIMS
        cursor = self.cursor
        try:
            while self.string[cursor] in DELIMS:
                cursor +=1
            return cursor
        except IndexError:
            return len(self)

    def find_next_delim(self):
        global DELIMS
        cursor = self.cursor

        if self.string[cursor] in DELIMS:
            return self.find_next_non_delim()

        try:
            while self.string[cursor] not in DELIMS:
                cursor +=1
            while self.string[cursor].isspace():
                cursor +=1
            return cursor
        except IndexError:
            return len(self)

    def find_previous_delim(self):
        global DELIMS
        cursor = self.cursor
        while cursor and self.string[cursor] in DELIMS:
            cursor -= 1
        while cursor and self.string[cursor] not in DELIMS:
            cursor -=1
        return cursor

    def inner_word(self):
        return slice(self.find_previous_delim() + 1, self.find_next_delim())

    def inner_WORD(self):
        start = self.string.rfind(' ', 0, self.cursor + 1)
        if start == -1:
            start = 0
        else:
            start +=1
        stop = self.string.find(' ', self.cursor + 1)
        if stop == -1:
            stop = len(self.string)
        return slice(start, stop)

    def find_next_token(self):
        cursor = self.cursor
        for off in self._token_list:
            if off > cursor:
                return off

    def find_previous_token(self):
        cursor = self.cursor
        for idx, off in enumerate(self._token_list):
            if off > cursor:
                return off

    def __getitem__(self, key):
        return self.string[key]

    def __delitem__(self, key):
        with self:
            if isinstance(key, int):
                start = key
                stop = key + 1
            elif isinstance(key, slice):
                start  = key.start or 0
                stop = key.stop or len(self)
            else:
                raise TypeError(f'{key = } {type(key) = } expected int or slice.')

            _string = self.string
            self.string = _string[:start] + _string[stop:]

    def __setitem__(self, key, value):
        with self:
            if isinstance(key, slice):
                start = key.start or 0
                stop = key.stop or len(self)
            elif isinstance(key, int):
                start = key
                stop = start + 1
            else:
                raise TypeError(f'{key = } {type(key) = } expected int or slice.')
            self.string = self._string[:start] + value + self._string[stop:]

########    saving mechanism     e#########################################

# Saving mechanism
    def save(self):
        assert self.path is not None
        self._repr = None
        self.path.write_text(self.string)
        self._states.append(self.string)
        if self._lsp_server:
            self._lsp_server.text_document_did_save(self._path_as_uri, self.string) 

    def save_as(self, new_path, override=False):
        from pathlib import Path
        new_path = Path(new_path).resolve()

        if not new_path.exists():
            self.path = new_path
            self.path.touch()
            self.save()
        else:
            if not new_path.is_file():
                if new_path.is_dir():
                    raise IsADirectoryError('cannot write text onto a directory!')
                raise FileExistsError('this file exists and is not a file nor a dir!')

            if override or not new_path.exists():
                self.path = new_path
                self.save()
            else:
                raise FileExistsError('Add ! in interface or override=True in *kwargs ....')
        if self._lsp_server:
            self._lsp_server.text_document_did_save(self._path_as_uri, self.string) 

    @property
    def unsaved(self):
        if not self.modifiable:
            return False
        if self.path and self.path.exists() and (last_saved := self._states[-1]):
            return last_saved != self.string != '\n'
        return self.string != '\n'

    def find_normal_l(self):
        try:
            if self.string[self.cursor+1] != '\n':
                return self.cursor + 1
        except IndexError:
            return self.cursor

    def find_normal_h(self):
        if self.cursor == 0:
            return 0
        if self.string[self.cursor - 1] == '\n':
            return self.cursor
        return self.cursor - 1

    def move_cursor(self, target):
        self.cursor = self.find(target)

    def find(self, target):
        if   target == 'B' : return self.find_normal_B()
        elif target == 'b' : return self.find_previous_delim()
        elif target == 'h' : return self.find_normal_h()
        elif target == 'j' : return self.find_normal_j()
        elif target == 'k' : return self.find_normal_k()
        elif target == 'l' : return self.find_normal_l()
        elif target == 'w' : return self.find_next_delim()
        elif target == 'W' : return self.find_next_WORD()
        elif target == 'G' : return len(self)
        elif target == 'gg': return 0
        elif target == 'e' : return self.find_end_of_word()
        elif target == 'E' : return self.find_end_of_WORD()
        elif target == '$' : return self.find_end_of_line()
        elif target == '0' : return self.find_begining_of_line()
        elif target == '_' : return self.find_first_non_blank_char_in_line()
        elif target == ')' : return self.find_next_token()
        else: raise RuntimeError('vy internal error: not a valid motion')

    def __str__(self):
        return ('writeable ' if self.modifiable else 'read-only ') + self.__class__.__name__ 
        
    def __repr__(self):
        return f'{self}(cursor={self.cursor})'

    @property
    def header(self):
        if not self._repr:
            if (pth := self.path):
                try:
                    self._repr = f'{self}: {pth.relative_to(pth.cwd(), walk_up=True)}'
                except:
                    self._repr = f'{self}: {pth.resolve()}'

            else:
                self._repr = f'{self}: ( undound to file system )'
        return self._repr

    @property
    def footer(self):
        current_state = self._string
        known_status = self._states
        return ('( original state )' if current_state == known_status[0]
                else '( saved )' if current_state == known_status[-1]
                else '( edited )') + str(self.undo_list)


    @property
    def _path_as_uri(self):
        return f'file://{self.path}' if self.path else None

    def _test_all_assertions(self):
        assert (_string := self._string) or (_string := ''.join(self._splited_lines))
        assert (_splited_lines := self._splited_lines) or (_splited_lines := _string.splitlines(True))
        assert (_number_of_lin := self._number_of_lin)

        assert ''.join(_splited_lines) == _string
        assert self._lenght == len(self) == len(_string)

        assert _number_of_lin == len(_splited_lines) == len(self.lines_offsets)
        assert self._cursor == self.lines_offsets[self.current_line_idx] + self.cursor_lin_col[1] - 1
#        assert self.lines_offsets == self.generate_properties()

    def lexer(self, code):
        for line in code.splitlines(True):
            yield 0, "", line


    
