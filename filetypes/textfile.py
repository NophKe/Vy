from multiprocessing import Process, Manager, Queue
from vy.screen import get_prefix
from vy import keys as k
DELIMS = ' .{}()[]():\n'

def set_lexer(buffer):
    from vy.global_config import DONT_USE_PYGMENTS_LIB
    if DONT_USE_PYGMENTS_LIB:
        return lambda: [(0, '', val) for val in buffer._string.splitlines(True)]
    from pygments.lexers import guess_lexer_for_filename as guess_lexer
    from pygments.util import  ClassNotFound
    try:
        _lexer = guess_lexer(str(buffer.path), buffer._string).get_tokens_unprocessed
    except ClassNotFound:
        _lexer = guess_lexer('text.txt', buffer._string).get_tokens_unprocessed
    return lambda : _lexer(buffer._string)

class TextFile:
    """This is the class that most of files buffers should use, 
    and should be preferably yielded by editor.cache[].
    Inherit from it to customize it.
    there should be a callback register to come.
    """
    def __init__(self, set_number=True, set_wrap=False, set_tabsize=4, 
                cursor=0, init_text='', path=None, **kwargs):

        #### UNDO MECANISME ####
        self._no_undoing = False
        self.redo_list = list()
        self.undo_list = list()

        self.path = path
        self.cursor = cursor
        self._string = init_text


        #### WiNDOW GENERATOR ####
        self.lexer = set_lexer(self) 
        self.set_wrap = set_wrap
        self.set_number = set_number
        self.set_tabsize = set_tabsize

        #### WIP ####

        self._lexer_request = Queue()
        self._lexed_away = Queue()
        self._lexed_away.cancel_join_thread()
        self.PROC = Process(target=self.PROC_lexed_string,
                            args=(self._lexed_away, self._lexer_request),
                            daemon=True)
        self.PROC.start()

        #### CACHED PROPERTIES ####
        self._splited_lines = list()
        self._lexed_lines = list()
        self._lines_offsets = list()

        self.motion_commands = {
           'b'         : self.find_previous_delim, k.S_left    : self.find_previous_delim,
           'h'         : self.find_normal_h, k.left      : self.find_normal_h,
           'j'         : self.find_normal_j,     '\r'        : self.find_normal_j,
           k.down      : self.find_normal_j, 'k':    self.find_normal_k,
           k.up:   self.find_normal_k, 'l':    self.find_normal_l,
           k.right:    self.find_normal_l, ' ':    self.find_normal_l,
           'w':    self.find_next_delim, k.S_right: self.find_next_delim,
           'W':    self.find_next_WORD, k.C_right: self.find_next_WORD,
           'G':    lambda: len(self), 'gg':   lambda: 0,
           'cursor': lambda self: self.cursor, 'e':    self.find_end_of_word,
           'E':    self.find_end_of_WORD, '$':    self.find_end_of_line,
           '0':    self.find_begining_of_line, '_':    self.find_first_non_blank_char_in_line,
           }

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
        if key == 'G'       : return len(self)
        if key == 'gg'      : return 0
        if key == 'cursor'  : return self.cursor
        if key == 'e'       : return self.find_end_of_word()
        if key == 'E'       : return self.find_end_of_WORD()
        if key == '$'       : return self.find_end_of_line()
        if key == '0'       : return self.find_begining_of_line()
        if key == '_'       : return self.find_first_non_blank_char_in_line()

    def find_end_of_line(self):
        offset = self._string.find('\n', self.cursor)
        if offset == -1:
            return len(self)
        return offset

    def find_end_of_word(self):
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

            #if (start :) > len(self): # Not Allowed in Cython
            start = self.cursor + 2
            if start > len(self): # Allowing Cython
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
        char = ''
        pos = self.cursor
        if self.cursor > 0:
            self.seek(pos - 1)
        else:
            return 0
        while True:
            char = self.read(1)
            if char == '\n':
                rv = self.tell()
                self.seek(pos)
                return rv
            next_pos = self.tell() - 2
            if next_pos < 0:
                self.seek(pos)
                return 0
            else:
                self.seek(next_pos)

    def find_first_non_blank_char_in_line(self):
        pos = self.tell()
        self.seek(self.find_begining_of_line())
        rv = self.find_next_non_blank_char()
        self.seek(pos)
        return rv

    def find_next_non_blank_char(self):
        pos = self.cursor
        while self._string[pos].isspace():
            if pos == len(self):
                break
            pos += 1
        return pos

    def find_normal_k(self):
        cursor = self.cursor
        on_col=1
        #while (line_start := cursor - on_col ) >= 0: # Allowing Cython
        line_start = cursor - on_col
        while line_start >= 0:
            if self[line_start] == '\n':
                break
            else:
                on_col += 1
                line_start = cursor - on_col # Allowing cython
        else:
            return 0

        previous_line = int(line_start) - 1
        while previous_line >= 0:
            if self[previous_line] == '\n':
                break
            else:
                previous_line -= 1
        else:
            return 0

        new_cursor = int(previous_line) +1
        while new_cursor <= previous_line + on_col -1:
            if self[new_cursor] == '\n':
                return new_cursor
            else:
                new_cursor += 1
        return new_cursor


    def find_normal_j(self):
        lin, col = self.cursor_lin_col
        if lin+1 >= len(self.lines_offsets):
            return self.cursor
        next_lin_offset = self.lines_offsets[lin+1]
        max_offset = next_lin_offset + len(self.splited_lines[lin+1])
        if next_lin_offset + col > max_offset:
            return max_offset
        return next_lin_offset + col - 1

    def find_normal_l(self):
        if self[self.cursor] == '\n':
            return self.cursor
        elif self.cursor < len(self):
            return self.cursor + 1

    def find_normal_h(self):
        if self.cursor == 0:
            return 0
        if self._string[self.cursor - 1] == '\n':
            return self.cursor
        return self.cursor - 1

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
        while self._string[cursor] in DELIMS:
            if cursor == len(self):
                return cursor
            cursor +=1
        return cursor

    def find_next_delim(self):
        global DELIMS
        cursor = self.cursor
        
        if self[cursor] in DELIMS:
            return self.find_next_non_delim()

        while self._string[cursor] not in DELIMS:
            if cursor == len(self):
                return cursor
            cursor +=1
        while self._string[cursor].isspace():
            if cursor == len(self):
                return cursor
            cursor +=1
        return cursor

    def find_previous_delim(self):
        global DELIMS
        cursor = self.cursor
        while self._string[cursor] in DELIMS:
            cursor -= 1
        while self._string[cursor] not in DELIMS:
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
        stop = self._string.find(' ', self.cursor + 1)
        if stop == -1:
            stop = len(self.string)
        return slice(start, stop)

    def current_line(self):
        start = self.find_begining_of_line()
        stop = self.find_end_of_line()
        if stop < len(self):
            stop +=1
        return slice(start, stop)

    def suppr(self):
        """Like the key strike, deletes the character under the cursor."""
        string = self._string
        cur = self.cursor
        self.string  = f'{string[:cur]}{string[cur + 1:]}'

    def backspace(self):
        """Like the key strike, deletes the left character at the cursor."""
        if self.cursor > 0:
            self.cursor -= 1
            self.suppr() 

    def insert(self, text):
        """Inserts text at the cursor position.
        Cursor will move at the and of it."""
        string = self._string
        cur = self.cursor
        self.string = f'{string[:cur]}{text}{string[cur:]}'
        self.cursor += len(text)

    def write(self, text):
        assert isinstance(text, str)
        if text:
            self.string = self._string[:self.cursor] + text + self._string[self.cursor + len(text):]
            self.cursor = self.cursor + len(text)

    def getvalue(self):
        return self._string

    def read(self, nchar= -1):
        if nchar == -1:
            rv = self._string[self.cursor:]
            self.cursor = len(self.string)
        else:
            rv = self._string[self.cursor:(self.cursor + nchar)]
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

    @property
    def cursor_lin_col(self):
        """A tupple representing the actual cursor (line, collumn),
        lines are 0 based indexed, and cols are 1-based.
        """
        lin, off = self.cursor_lin_off
        col = self.cursor - off + 1
        return lin, col

    @property
    def cursor_lin_off(self):
        """A tupple (cursor_line, ),
        lines are 0 based indexed, and cols are 1-based.
        """
        cursor = self.cursor
        lin = offset = 0
        for lin, offset in enumerate(self.lines_offsets):
            if offset == cursor:
                return lin, offset
            if offset > cursor:
                return lin - 1, self.lines_offsets[lin - 1 ]
        else:
            return lin, offset

    @property
    def cursor_line(self):
        """The zero-based number indexing the current line."""
        cursor = self.cursor
        lin = offset = 0
        for lin, offset in enumerate(self.lines_offsets):
            if offset == cursor:
                return lin
            if offset > cursor:
                return lin - 1
        else:
            return lin

    @property
    def lines_offsets(self):
        if not self._lines_offsets:
            offset = 0
            linesOffsets = self._lines_offsets
            for line in self._string.splitlines(True):
                linesOffsets.append(offset)
                offset += len(line)
            #self._lines_offsets = linesOffsets
        return self._lines_offsets

    @property
    def splited_lines(self):
        if not self._splited_lines:
            self._splited_lines = self._string.splitlines()
        return self._splited_lines

    @property
    def number_of_lin(self):
        """Number of lines in the buffer"""
        return len(self.lines_offsets)

    def move_cursor(self, offset_str):
        self.cursor = self._get_offset(offset_str)
    
    def __len__(self):
        return len(self._string) - 1

    def __getitem__(self, key):
        if isinstance(key, str):
            key = self._get_range(key)
        return self._string.__getitem__(key)

    def _get_range(self,key):
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
        if isinstance(key, int):
            return key
        elif isinstance(key, str) and key.startswith('#'):
            current_line_start = self.lines_offsets[self.cursor_line]
            # now that .lines_offsets is computed, will use ._lines_offsets instead

            if key == '#.':
                return current_line_start
            elif key.startswith('#+'):
                try:
                    entry = self._lines_offsets.index(current_line_start) + int(key[2:])
                    return self._lines_offsets[entry]
                except (IndexError, ValueError):
                    return len(self)
            elif key.startswith('#-'):
                try:
                    entry = self._lines_offsets.index(current_line_start) - int(key[2:])
                    return self._lines_offsets[entry]
                except (IndexError, ValueError):
                    return len(self)

            try:
                return self.lines_offsets[int(key[1:])]
            except IndexError:
                return len(self) # is this ever reached ?
        #return self.motion_commands[key](self)
        return self.offset_finder(key)

    def __delitem__(self, key):
        if isinstance(key, int):
            if key >=0 and key < len(self):
                self.string = self._string[0:key] + self._string[key+1:]
            else: raise IndexError('Vy Runtime: string index out of range')

        elif isinstance(key, slice):
            if not key.start:   start = 0
            else:               start = key.start
            if not key.stop:    stop = len(self._string) - 1
            else:               stop = key.stop
            self.string = f'{self._string[:start]}{self._string[stop:]}'
            if key.start < self.cursor <= key.stop:
                self.cursor = key.start

        elif isinstance(key, str):
            key = self._get_range(key)
            self.__delitem__(key)
            return
        else: raise TypeError

    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = self._get_range(key)
        if isinstance(key, slice):
            start = key.start
            stop = key.stop
        elif isinstance(key, int):
            start = key
            stop = start + 1
        self.string = f'{self._string[:start]}{value}{self._string[stop:]}'
######## UNDO MECANISM ####################################################

    @property
    def string(self):
        return self._string

    @string.setter
    def string(self, value):
        self._string = value
        self._lines_offsets.clear()
        if self.redo_list:
            self.redo_list = list()
        self._splited_lines.clear()
        self._lexed_lines.clear()

        self.PROC.kill()
        self._lexer_request = Queue()
        self._lexed_away.cancel_join_thread()
        self._lexed_away = Queue()
        self.PROC = Process(target=self.PROC_lexed_string,
                            args=(self._lexed_away, self._lexer_request),
                            daemon=True)
        self.PROC.start()

    
    def compress_undo_list(self):
        self.undo_list = [item 
                            for index, item in enumerate(self.undo_list) 
                                if index % 2 == 0]
        
    def start_undo_record(self):
        self._no_undoing = False
        self.set_undo_point()
    
    def stop_undo_record(self):
        self._no_undoing = True
        self.set_undo_point()

    def set_undo_point(self):
        actual_txt, actual_cur = self._string, self.cursor
        actual_off = self.lines_offsets

        if not self.undo_list:
            self.undo_list.append((actual_txt, actual_cur, actual_off))
            return
        last_txt, _x, _y = self.undo_list[-1]
        if actual_txt != last_txt:
            self.undo_list.append((actual_txt, actual_cur, actual_off))

    def undo(self):
        if not self.undo_list:
            return
        txt, pos, off = self.undo_list.pop()
        self.redo_list.append((self._string, self.cursor,
                                self.lines_offsets))
        self.string = txt
        self.cursor = pos
        self._lines_offsets = off
    
    def redo(self):
        if not self.redo_list:
            return
        txt, pos, off = self.redo_list.pop()
        self.undo_list.append((txt, pos, off))
        self.string = txt
        self.cursor = pos
        self._lines_offsets = off

    def PROC_lexed_string(self, send_queue, recv_queue):
        retval = list()
        line = list()
        for offset, tok, val in self.lexer():
            if '\n' in val:
                for token_line in val.splitlines(True):
                    if token_line.endswith('\n'):
                        token_line = token_line[:-1] + ' '
                        line.append((token_line, repr(tok)))
                        retval.append(line)
                        line = list()
                    else:
                        line.append((token_line, repr(tok)))
            else:
                line.append((val, repr(tok)))
        if line: #No eof
            retval.append(line)
        while True:
            lexed_string = ''
            index = recv_queue.get()
            try:
                line = retval[index]
            except IndexError:
                send_queue.put((index, None))
                continue
            for text, token in line:
                lexed_string = f'{lexed_string}{get_prefix(token)}{text}\x1b[0m'
            send_queue.put((index,lexed_string))

    def get_lexed_line(self, index):
        #assert self.PROC.is_alive()
        self._lexer_request.put_nowait(index)
        idx, ret = self._lexed_away.get()
        if ret is None:
            raise IndexError
        return idx, ret
#       if not self._post_lexed_lines:
#           self._post_lexed_lines = [None for _ in range(self.number_of_lin)]
#       if self._post_lexed_lines[index]:
#          return self._post_lexed_lines[index]

#       lexed_string = ''
#       try:
#           lexed_line = self.lexed_lines[index]
#       except IndexError:
#           if self.PROC.is_alive():
#               self.PROC.join(3)
#           if self.PROC.is_alive():
#               raise RuntimeError
#           lexed_line = self.lexed_lines[index]
#       for text, token in lexed_line:
#           lexed_string = f'{lexed_string}{get_prefix(token)}{text}\x1b[0m'
#       self._post_lexed_lines[index] = lexed_string
#       return lexed_string
    
    @property
    def lexed_lines(self) :
        #if self.PROC.is_alive():
            #self.PROC.join()
#           if self._lexer_queue.empty():
                retval = list()
                line = list()
                for offset, tok, val in self.lexer():
                    if '\n' in val:
                        for token_line in val.splitlines(True):
                            if token_line.endswith('\n'):
                                token_line = token_line[:-1] + ' '
                                line.append((token_line, repr(tok)))
                                retval.append(line)
                                line = list()
                            else:
                                line.append((token_line, repr(tok)))
                    else:
                        line.append((val, repr(tok)))
                if line: #No eof
                    retval.append(line)
                self._lexed_lines = retval
                return self.lexed_lines
#           else:
#               txt_hash, retval = self._lexer_queue.get(False)
#               if txt_hash == hash(self._string):
#                   self._lexed_lines = retval
#                   return self._lexed_lines
#               return self.lexed_lines
#       return self._lexed_away

    def __repr__(self):
        return f"writeable buffer: {self.path.name if self.path else 'undound to file system'}"

# Saving mechanism
    def save(self):
        assert self.path is not None
        self.path.write_text(self._string)

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
            if self.string and self._string != '\n':
                return True
        elif self.path.read_text() != self.string != '\n':
            return True
        return False
