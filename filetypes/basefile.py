from vy import keys as k
from threading import Condition, Event, Lock, RLock

DELIMS = ' ,;:/!%.{}()[]():\n'

class DummyLine:
    """
    This class provides a simple interface around a line oriented
    buffer. It is meant to be used for simple use-case like implementing
    custom input() function. No optimization, nor locking is made around 
    the data.

    >>> x = DummyLine()
    >>> x.insert('FOO')
    >>> x.string
    >>> x.cursor = 0
    >>> x.insert('\n12345')
    >>> x.backspace()
    >>> x.string
    '\n1234'
    >>> x.cursor = 0
    >>> x.suppr()
    >>> x.string
    '1234'
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
        self.string  = f'{string[:cur]}{string[cur + 1:]}'

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
    
    #
    # to make assert statements happy, 
    # allways update STRING _before_ CURSOR
    #

    @string.setter
    def string(self, value):
        assert value.endswith(self.ending)
        self._string = value

    @cursor.setter
    def cursor(self, value):
        assert len(self) >= value >= 0
        self._cursor = value

    def __len__(self):
        return len(self._string) - len(self.ending)

class TextLine(DummyLine):
    ending = '\n'

########    End of DummyLine class and subclasses  #########################

class BaseFile:
    r"""
    BaseFile is... ( well... ) the basis for what is usually called a «buffer» 
    in the in the Vi-like editors jargon.

    It mix the classical expected features of a mutable string with some traditionnal 
    concepts of vim buffers, like mouvements.
    
    >>> file = BaseFile(init_text='Hello World\n\t42\t\nno End-of-file?', cursor=0)
    >>> file.move_cursor('w')           # moves to next word ( regex \b )
    >>> assert file[:11] == file[':$']  # vim style buffer slice ( regex ^.*$ ) 

    All of its public methods are atomic (using an internal threading.RLock object).
    If you need to keep the object around, you can acquire its internal lock by 
    using it as a context manager.
    
    >>> with file:
    ...     assert file.number_of_lin == len(file.splited_lines) == len(file.lines_offsets)
    >>> # the number of lines in the buffer  ==  lenght of list of lines 
    >>> #     == lenght of the list of all the offsets where start a single line

    To modify the content of the buffer: use one of its three setters properties. (string, 
    current_line and cursor). Any modifications of one of those properties will immediatly 
    invalidate any other property that depend on it. 

    >>> file.splited_lines
    >>> file.current_line = '' # what if I forget line ending
    >>> file.current_line = '\n' # what if I forget line ending
    >>> file.cursor_lin_col
    >>> # Now lets modify it.
    >>> file.cursor = file.lines_offsets[file.number_of_lin - 1]
    >>> file.insert('junk')
    >>> # TODO carrefully review next results
    >>> file.current_line
    >>> file.splited_lines
    >>> file.cursor_lin_col

    Properties being lazily evaluated, a few «fast paths» are provided 
    to speed up common operations upon the internal data structure. Do 
    not rely on them! Being lazily computed, a lot of the properties 
    assert themselves towards each other. Some assertions are clearly 
    redundant but will be maintained for correctness. Moreover speed 
    on that matter may strongly depend on you python implementation.

    >>> file.insert_newline()
    >>> file.insert('\n')

    By definition, one line should allways end by a newline. Also one 
    empty line is represented by EMPTY STRING + NEWLINE.
    The newline character has no special treatment anywhere in the file,
    you can delete them and insert new ones any time, but the last newline 
    character that ends the buffer cannot be deleted.
    
    >>> file.backspace()
    >>> file.suppr()
    >>> file.suppr()

    A Buffer may also be used as a replacement for a file object.

    >>> file.write('中国')
    >>> file.seek(0)
    >>> file.write('over_write')
    >>> file.read()

    One may also consider a buffer as a mutable sequence suitable as a 
    remplacement of the immutable string.

    >>> file[0:10]
    >>> file[0:8] = 'too big to fit in there'
    >>> file[0] = 'never '
    >>> file[:29] 
    
    NOTE: the word «offset» will be used to speak about characters and their
         positions, whereas «index» will be used for line numbers.
    """

    modifiable = True
    actions = {}
    ending = '\n'   
    
    @property
    def string(self):
        """
        string is a property returning the internal buffer.

        Modifying its value triggers the registered callbacks.
        """
        with self._lock:
            if not self._string:
                assert self._splited_lines
                self._string = ''.join(self._splited_lines)
            return self._string

    @property
    def cursor_lin_col_unsafe(self):
        r"""
        A tupple representing the actual the lenght and the cursor 
        (len, line, collumn), lines are 0 based indexed, and cols are 1-based.

        This method does not acquire the internal lock as it does not
        modify anything. Any inconsistency caused by the interference
        of another thread (if noticed) will cause the raising of a RuntimeError
        exception, as this Exception is silently ignored by the thread
        in charge of screen printing.
        
        NOTE: See TextFile.get_lexed_line() parameters.
        
        """
        try:
            cursor = self._cursor
            splited_line = self._splited_lines
            line_off = self._lines_offsets
            lin_col = self._cursor_lin_col

            if lin_col:
                if splited_line:
                    return len(splited_line), lin_col[0], lin_col[1]
                if line_off:
                    return len(line_off), lin_col[0], lin_col[1]

            if splited_line:
                previous_line = 0
                offset = 0
                for lin, value in enumerate(splited_line):
                    if offset == cursor:
                        return len(splited_line), lin, cursor - offset + 1
                    if offset > cursor:
                        return len(splited_line), lin - 1, cursor - previous_line + 1
                    previous_line, offset = offset, offset + len(value)
                else:
                    return len(splited_line), lin, cursor - offset +1

            elif line_off:
                for lin, offset in enumerate(line_off):
                    if offset == cursor:
                        return len(line_off), lin, cursor - offset + 1
                    if offset > cursor:
                        return len(line_off), lin - 1, cursor - self._lines_offsets[lin - 1 ] + 1
                else:
                    return len(line_off), lin, cursor - offset +1
        except:
            raise RuntimeError
        raise RuntimeError

    @property
    def cursor_lin_col(self):
        """
        A tupple representing the actual cursor (line, collumn),
        lines are 0 based indexed, and cols are 1-based.
        
        This property should be the main api to modify the cursor.
        """
        with self._lock:
            if not self._cursor_lin_col:
                lin, off = self.cursor_lin_off
                #assert lin < self.number_of_lin
                col = self.cursor - off + 1
                self._cursor_lin_col = (lin, col)
            return self._cursor_lin_col

    @cursor_lin_col.setter
    def cursor_lin_col(self, pair_value):
        """
        A tupple representing the actual cursor (line, collumn),
        lines are 0 based indexed, and cols are 1-based.
        """
        with self._lock:
            old_lin, old_col = self.cursor_lin_col
            new_lin, new_col = pair_value
            assert new_col > 0
            assert self.number_of_lin > new_lin >= 0

            if old_lin == new_lin:
                if new_col > len(self.current_line):
                    new_col = len(self._current_line)
                self._cursor = self.lines_offsets[old_lin] + new_col
                self._cursor_lin_col = (old_lin, new_col)

            else:
                max_col = len(self.splited_lines[new_lin])
                line_off = self.lines_offsets[new_lin]
                max_cursor = line_off + max_col
                try:
                    assert self._lines_offsets[new_lin+1] == max_cursor
                except IndexError: 
                    pass
                
                if new_col > max_col:
                    self._cursor = max_cursor
                    self._cursor_lin_col = (new_lin, max_col)
                else:
                    self._cursor = line_off + new_col
                    self._cursor_lin_col = (new_lin, new_col)
                self._current_line = self.splited_lines[new_lin]

    @property
    def cursor_lin_off(self):
        """
        A tupple (cursor_line, offset_of_cursor_line),
        lines are 0 based indexed, and cols are 1-based.
        """
        with self._lock:
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
    def cursor_line(self):
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

        >>> rand = randint(0, x.number_of_lin-2)
        >>> assert (sum(len(lines) for lines in x.splited_lines[:rand]) == 
                        x.lines_offsets[rand])
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
        """
        This is the list of the lines contained in the buffer, each should 
        have a trailing newline.

        >>> rand = randint(0, x.number_of_lin-2)
        >>> assert (sum(len(lines) for lines in x.splited_lines[:rand]) == 
                        x.lines_offsets[rand])
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
                if self._splited_lines and self._lines_offsets:
                    assert len(self._splited_lines) == len(self._lines_offsets)
                    rv = len(self._splited_lines)
                elif self._string and self._splited_lines:
                    rv = self._string.count('\n') 
                    assert rv == len(self.splited_lines)#, f'{len(self.splited_lines) = } {rv = }'
                elif self._string:
                    rv = self._string.count('\n')
                    assert rv == len(self.splited_lines)#, f'{len(self.splited_lines) = } {rv = }'
                else:
                    return len(self.splited_lines)
                self._number_of_lin = rv
            return self._number_of_lin

    def suppr(self):
        """
        Like the key strike, deletes the character under the cursor.
        """
        with self._lock:
            if (cur_lin := self._current_line) and len(cur_lin) > 1:
                lin, col = self.cursor_lin_col
                self.current_line  = f'{cur_lin[:col]}{cur_lin[col + 1:]}'
            else:
                string = self.string
                cur = self.cursor
                self.string  = f'{string[:cur]}{string[cur + 1:]}'

    def backspace(self):
        """
        Like the key strike, deletes the left character at the cursor.
        """
        with self._lock:
            if self.cursor > 0:
                self.cursor -= 1
                self.suppr() 

    def insert(self, text):
        """
        Inserts text at the cursor position.
        Cursor will move to end of inserted text.
        """
        with self._lock:
            #assert False, f'{text = }'
            if '\n' in text:
                string = self.string
                cur = self._cursor
                self.string = f'{string[:cur]}{text}{string[cur:]}'
                self.cursor += len(text)
            else:
                lin, col = self.cursor_lin_col
                string = self.current_line
                self._string = ''
                cur = col - 1
                self._cursor += len(text)
                self._cursor_lin_col = (lin, col + len(text))
                self.current_line = f'{string[:cur]}{text}{string[cur:]}'

    def __init__(self, set_number=True, set_wrap=False, 
                set_tabsize=4, cursor=0, init_text='', 
                path=None):
        self.path = path
        self.set_wrap = set_wrap
        self.set_number = set_number
        self.set_tabsize = set_tabsize

        self._string = ''
        self._cursor = cursor
        self._number_of_lin = 0
        self._lenght = None
        self._current_line = ''
        self._lines_offsets = list()
        self._splited_lines = list()
        self._cursor_lin_col = ()
        self._lock = RLock()
        self.update_callbacks = list()
        self.pre_update_callbacks = list()
        self.string = init_text
        self.cursor = cursor

        self._no_undoing = False
        self.redo_list = list()
        self.undo_list = list()
        #self.pre_update_callbacks.append(self.set_undo_point)

        self.motion_commands = {
           'b'          : self.find_previous_delim,
           k.S_left     : self.find_previous_delim,
           'h'          : self.find_normal_h,
           k.left       : self.find_normal_h,
           'j'          : self.find_normal_j,
           '\r'         : self.find_normal_j,
           k.down       : self.find_normal_j,
           'k'          : self.find_normal_k,
           k.up         : self.find_normal_k,
           'l'          : self.find_normal_l,
           k.right      : self.find_normal_l,
           ' '          : self.find_normal_l,
           'w'          : self.find_next_delim,
           k.S_right    : self.find_next_delim,
           'W'          : self.find_next_WORD,
           k.C_right    : self.find_next_WORD,
           'G'          : lambda: len(self),
           'gg'         : lambda: 0,
           'cursor'     : lambda self: self.cursor,
           'e'          : self.find_end_of_word,
           'E'          : self.find_end_of_WORD,
           '$'          : self.find_end_of_line,
           '0'          : self.find_begining_of_line,
           '_'          : self.find_first_non_blank_char_in_line,
           }

    def __enter__(self):
        self._lock.acquire()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
        return False

    def __len__(self):
        with self._lock:
            if self._lenght is None:
                if self._string:
                    self._lenght = len(self._string) - len(self.ending)
                elif self._splited_lines:
                    self._lenght = sum(len(line) for line in self._splited_lines) - len(self.ending)
                else:
                    raise BaseException('vy internal error')
            return self._lenght

    #def delete_line(self, index):
        #with self._lock:
            #assert self.splited_lines 
            #assert self.number_of_lin
            #self._splited_lines.pop(index)
            #self._cursor_lin_col = ()
            #self._number_of_lin = self._number_of_lin - 1
            #self._lines_offsets.clear()
            #self._string = ''

    def insert_newline(self):
        [func() for func in self.pre_update_callbacks]
        with self._lock:
            assert self._lenght is not None # test while triggering computation
            assert self._splited_lines

            lin, col = self.cursor_lin_col
            top = (self._splited_lines[lin])[:col-1] + '\n'
            bottom = (self._splited_lines[lin])[col-1:]
            self._lines_offsets.clear()
            self._string = ''

            self._splited_lines.insert(lin, top)
            self._splited_lines[lin+1] = bottom
            self._current_line = bottom
            self._cursor_lin_col = (lin+1, 1)
            self._cursor += 1
            self._number_of_lin = self._number_of_lin + 1
            self._lenght += 1

        [func() for func in self.update_callbacks]

    def insert_newline(self):
        return self.insert('\n')
    @property
    def current_line(self):
        with self._lock:
            if not self._current_line:
                self._current_line = self.splited_lines[self.cursor_line]
                assert self._current_line.endswith('\n')
                assert '\n' not in self._current_line[:-1]
            return self._current_line

    @current_line.setter
    def current_line(self, value):
        [func() for func in self.pre_update_callbacks]
        with self._lock:
            assert value and value.endswith('\n'), f'{value = }'
            assert '\n' not in value[:-1], f'{value = }'

            lin, _ = self.cursor_lin_col
            cur_lin = self._splited_lines[lin]
            if self._lenght is not None:
                delta = len(old_val) - len(value)
                self._lenght -= delta

            self._splited_lines[lin] = value
            self._string = ''
            self._current_line = value
            self._lines_offsets.clear()
        [func() for func in self.update_callbacks]

    @property
    def cursor(self):
        """
        The cursor is a property that returns the position of 
        the cursor as an opaque integer value.
        >>> len('国')
        """
        with self._lock:
            return self._cursor

    @cursor.setter
    def cursor(self, value):
        with self._lock:
            if self._cursor != value:
                if self._lenght is not None:
                    assert self._lenght >= value, f'{self._lenght =} {value =} {(self) = }'
                    assert value >= 0, f'{value =} {len(self)}'
                self._current_line = ''
                self._cursor_lin_col = ()
                self._cursor = value


    @string.setter
    def string(self, value):
        assert isinstance(value, str)
        assert self.modifiable
        [func() for func in self.pre_update_callbacks]
        with self._lock:
            self._current_line = ''
            self._number_of_lin = 0
            self._splited_lines.clear()
            self._lines_offsets.clear()
            if not value.endswith(self.ending):
                self._string = value + self.ending
                self._lenght = len(value)
            else:
                self._string = value
                self._lenght = len(value) - 1
        [func() for func in self.update_callbacks]



### TODO - currently undo is undocumented and disabled
###        activating it leeds to memory failure soon or later
### 
### - check available memory
### - special case very large files
### - use swap temporary files

    def compress_undo_list(self):
        self.undo_list = [
            item for index, item in enumerate(self.undo_list) 
            if index % 2 == 0]
        
    def start_undo_record(self):
        self._no_undoing = False
        self.set_undo_point()
    
    def stop_undo_record(self):
        self._no_undoing = True
        self.set_undo_point()

    def set_undo_point(self):
        if self._no_undoing:
            return
        if (not self.undo_list) or (self.undo_list and self.undo_list[-1][0] != self.string):
            self.undo_list.append((self.string[:], int(self.cursor), self.lines_offsets[:]))

    def undo(self):
        self._string, self.cursor, self._lines_offsets = self.undo_list.pop()

    def redo(self):
        if not self.redo_list:
            return
        txt, pos, off = self.redo_list.pop()
        self.undo_list.append((txt, pos, off))
        self.string = txt
        self.cursor = pos
        self._lines_offsets = off

    def offset_finder(self, key):
        if key == 'b'       : return self.find_previous_delim()
        if key == k.S_left  : return self.find_previous_delim()
        if key == 'h'       : return self.find_normal_h()
        if key == k.left    : return self.find_normal_h()
        if key == 'j'       : return self.find_normal_j()
        if key == '\r'      : return self.find_normal_j()
        if key == k.down    : return self.find_normal_j()
        if key == 'k'       : return self.find_normal_k()
        if key == k.up      : return self.find_normal_k()
        if key == 'l'       : return self.find_normal_l()
        if key == k.right   : return self.find_normal_l()
        if key == ' '       : return self.find_normal_l()
        if key == 'w'       : return self.find_next_delim()
        if key == k.S_right : return self.find_next_delim()
        if key == 'W'       : return self.find_next_WORD()
        if key == k.C_right : return self.find_next_WORD()
        if key == 'G'       : return len(self) - 1
        if key == 'gg'      : return 0
        if key == 'cursor'  : return self.cursor
        if key == 'e'       : return self.find_end_of_word()
        if key == 'E'       : return self.find_end_of_WORD()
        if key == '$'       : return self.find_end_of_line()
        if key == '0'       : return self.find_begining_of_line()
        if key == '_'       : return self.find_first_non_blank_char_in_line()
        #raise RuntimeError(f'{key = } not a valid motion')
        raise RuntimeError #(f'{key = } not a valid motion')

    def find_end_of_line(self):
        r"""
        >>> x.string = "0____5\n___"
        >>> x.cursor = 0
        >>> x.find_end_of_line()
        6
        >>> x.find_end_of_line()
        6
        >>> x.cursor = 7
        >>> x.find_end_of_line()
        9
        """
        offset = self.string.find('\n', self.cursor)
        if offset == -1:
            return len(self)
        return offset

    def find_end_of_word(self):
        r"""
        This should correspond to normal mode 'e' motion.

        >>> x.cursor = 0
        >>> x.string = "foo,bar;baz.foo,bar/baz!foo%bar"
        >>> # breaks      ||  ||  ||  ||  ||  ||  ||  |             
        >>> # breaks      2|  6| 10| 14| 18| 22| 26| 30             
        >>> # breaks       3   7  11  15  19  23  27                
        >>> for expected in [2,3,6,7,10,11,14,15,18,19,22,23,26,27,30]:
        ...     assert _t(x, x.find_end_of_word()) == expected, f' *** {expected = } *** { x.cursor = }'
        """
        places = set()
        #if (start :self.cursor + 2) > len(self): # Not Allowed in Cython
        start = self.cursor + 2
        if start > len(self): # Allowing Cython
            return self.cursor
        global DELIMS
        for char in DELIMS:
            loc = self[start:].find(char)
            if loc > -1:
                loc += self.cursor
                places.add(loc+1)
        if places:
            return min(places)
        return self.cursor

    def find_end_of_WORD(self):
        start = self.cursor
        try:
            while self[start].isspace():
                start += 1

            start = self.cursor + 2
            if start > len(self):
                return self.cursor
            sp_offset = self[start:].find(' ')
            nl_offset = self[start:].find('\n')
            offset = min( (sp_offset, nl_offset,) )
            if offset == -1:
                return len(self)
            return start + offset
        except IndexError:
            return self.cursor

    def find_begining_of_line(self):
        with self._lock:
            return self.lines_offsets[self.cursor_line]

    def find_first_non_blank_char_in_line(self):
        pos = self.tell()
        self.seek(self.find_begining_of_line())
        rv = self.find_next_non_blank_char()
        self.seek(pos)
        return rv

    def find_next_non_blank_char(self):
        pos = self.cursor
        while self.string[pos].isspace() and pos < len(string):
            pos += 1
        return pos

    def find_normal_k(self):
        with self._lock:
            lin, col = self.cursor_lin_col
            if lin == 0:
                return self.cursor
            else:
                return (lin-1, col)

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
        cursor = self.cursor +1
        try:
            if not self[cursor].isspace(): 
                while not self[cursor].isspace(): 
                    cursor += 1
            while self[cursor].isspace(): 
                cursor += 1
            return cursor
        except IndexError:
            return cursor

    def find_next_word(self):
        cursor = self.cursor +1
        try:
            while not self[cursor] in DELIMS:
                cursor += 1
            while self[cursor].isspace(): 
                cursor += 1
            return cursor
        except IndexError:
            return cursor

    def find_first_char_of_word(self):
        if self.cursor == 0:
            return 0
        elif  self[self.cursor - 1].isspace():
            return self.cursor
        else:
            return self[:self.cursor].rfind(' ') + 1

    def find_normal_b(self):
        old_pos = self.tell()
        word_offset = self.find_first_char_of_word() 
        if word_offset == old_pos and word_offset != 0:
            self.seek(old_pos - 1)
            rv = self.find_first_char_of_word()
            self.seek(old_pos)
            return rv
        else:
            return word_offset

    def find_next_non_delim(self):
        global DELIMS
        cursor = self.cursor
        while self.string[cursor] in DELIMS:
            if cursor == len(self):
                return cursor
            cursor +=1
        return cursor

    def find_next_delim(self):
        global DELIMS
        cursor = self.cursor
        
        if self[cursor] in DELIMS:
            return self.find_next_non_delim()

        while self.string[cursor] not in DELIMS:
            if cursor == len(self):
                return cursor
            cursor +=1
        while self.string[cursor].isspace():
            if cursor == len(self):
                return cursor
            cursor +=1
        return cursor

    def find_previous_delim(self):
        global DELIMS
        cursor = self.cursor
        while self.string[cursor] in DELIMS:
            cursor -= 1
        while self.string[cursor] not in DELIMS:
            if cursor == 0:
                return cursor
            cursor -=1
        return cursor

    def inner_word(self):
        return slice(self.find_previous_delim(), self.find_next_delim())

    def INNER_WORD(self):
        start = self.string.rfind(' ', 0, self.cursor + 1)
        if start == -1:
            start = 0
        else:
            start +=1
        stop = self.string.find(' ', self.cursor + 1)
        if stop == -1:
            stop = len(self.string)
        return slice(start, stop)

    #def current_line(self):
        #start = self.find_begining_of_line()
        #stop = self.find_end_of_line()
        #if stop < len(self):
            #stop +=1
        #return slice(start, stop)


    def write(self, text):
        assert isinstance(text, str)
        if text:
            self.string = self.string[:self.cursor] + text + self.string[self.cursor + len(text):]
            self.cursor = self.cursor + len(text)
        return len(text)

    def getvalue(self):
        return self.string

    def read(self, nchar= -1):
        if nchar == -1:
            rv = self.string[self.cursor:]
            self.cursor = len(self.string)
        else:
            rv = self.string[self.cursor:(self.cursor + nchar)]
            self.cursor = self.cursor + nchar
        return rv

    def tell(self):
        return self.cursor

    def seek(self,offset=0, flag=0):
        assert isinstance(offset, int)
        assert isinstance(flag, int)
        if len(self) == 0:
            return 0
        max_offset = len(self)
        if (offset == 0 and flag == 2) or (offset > max_offset):
            self.cursor = max_offset
        elif 0 <= offset <= max_offset:
            self.cursor = offset

    def move_cursor(self, offset_str):
        with self._lock:
            new_val = self._get_offset(offset_str)
            if isinstance(new_val, int):
                self.cursor = new_val
            elif isinstance(new_val, tuple):
                self.cursor_lin_col = new_val
    
    def __getitem__(self, key):
        with self._lock:
            if isinstance(key, str):
                assert key #, f'{key = }'
                key = self._get_range(key)
#            assert ( isinstance(key, int) and key >= 0
#                   or isinstance(key, slice)) , f'{key = } {type(key) = }'
            return self.string[key]

    def _get_range(self,key):
        with self._lock:
            if ':' in key:
                start, stop = key.split(':', maxsplit=1)
                start = start.lstrip(':')
                stop = stop.rstrip(':')
                if not start:
                    start = 0
                if not stop:
                    stop = len(self)
                return slice(self._get_offset(start), self._get_offset(stop))
            return self._get_offset(key)

    def _get_offset(self, key):
        with self._lock:
### TODO this function should be protected against passsing string like '+-2'
            if isinstance(key, int):
                #assert len(self) >= key >= 0
                return key
            if not key:
                raise TypeError
            if isinstance(key, str):
                try:
                    line, current_line_start = self.cursor_lin_off
                    if key == '#.':
                        return current_line_start
                    elif key.startswith('#+'):
                        entry = line + int(key[2:])
                        return self.lines_offsets[entry]
                    elif key.startswith('#-'):
                        entry = line - int(key[2:])
                        return self.lines_offsets[entry]
                    elif key.startswith('#'):
                        index = int(key[1:])
                        return self.lines_offsets[index]
                    elif key.isdigit():
                        return int(key)
                    else:
                        try:
                            func = self.motion_commands[key]
                            return func()
                        except IndexError:
                            raise ValueError('Vy: not a valid motion.')
                        return self.offset_finder(key)
                except IndexError:
                    return None
                except ValueError:
                    raise BaseException(f'unrecognized offset {key = } {type(key) = }')

    def __delitem__(self, key):
        with self._lock:
            if isinstance(key, int):
                if key >=0 and key < len(self):
                    self.string = self.string[0:key] + self.string[key+1:]
                else:
                    raise IndexError('Vy Runtime: string index out of range')

            elif isinstance(key, slice):
                if not key.start:
                    start = 0
                else:
                    start = key.start
                if not key.stop:
                    stop = len(self.string) - 1
                else:
                    stop = key.stop
                self.string = f'{self.string[:start]}{self.string[stop:]}'

                if start < self.cursor <= stop:
                    self.cursor = start

            elif isinstance(key, str):
                key = self._get_range(key)
                del self[key]
            else:
                raise TypeError#(f'{key = } {type(key) = }')

    def __setitem__(self, key, value):
        with self._lock:
            if isinstance(key, str):
                key = self._get_range(key)
            if isinstance(key, slice):
                start = key.start
                stop = key.stop
            elif isinstance(key, int):
                start = key
                stop = start + 1
            self.string = f'{self.string[:start]}{value}{self.string[stop:]}'

    def __repr__(self):
        return f"writeable buffer: {self.path.name if self.path else 'undound to file system'}"

# Saving mechanism
    def save(self):
        assert self.path is not None
        self.path.write_text(self.string)

    def save_as(self, new_path=None, override=False):
        from pathlib import Path
        new_path = Path(new_path).resolve()
                
        if not new_path.exists():
            self.path = new_path
            self.path.touch()
            self.save()
        else:
            if not new_path.is_file():
                if not new_path.is_dir():
                    raise FileExistsError('this file exists and is not a file nor a dir!')
                else:
                    raise IsADirectoryError('cannot write text onto a directory!')
            else:
                if override: 
                    self.path = new_path
                    self.save()
                else:
                    raise FileExistsError('Add ! in interface or override=True in *kwargs ....')

    @property
    def unsaved(self):
        if self.path is None or not self.path.exists():
            if self.string and self.string != '\n':
                return True
        elif self.path.read_text() != self.string != '\n':
            return True
        return False

    def find_normal_l(self):
        r"""
        >>> x.string = "0____5\n_"
        >>> x.cursor = 0
        >>> x.find_normal_l()
        1
        >>> x.cursor = 5
        >>> x.find_normal_l()
        5
        >>> x.cursor = 7
        >>> _t(x, x.find_normal_l())
        7
        """
        try:
            if self.string[self.cursor+1] != '\n':
                return self.cursor + 1
        except IndexError:
            pass 
        return self.cursor

    def find_normal_h(self):
        r"""
        >>> x.string = "0____5\n___"
        >>> x.cursor = 0
        >>> x.find_normal_h()
        0
        >>> x.cursor = 7
        >>> x.find_normal_h()
        7
        """
        if self.cursor == 0:
            return 0
        if self.string[self.cursor - 1] == '\n':
            return self.cursor
        return self.cursor - 1

if __name__ == '__main__':
    x = BaseFile()
    def _t(result):
        global x
        x.cursor = result
        return result
    import doctest
    doctest.testmod()

