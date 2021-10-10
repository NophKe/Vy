DELIMS = ' .{}()[]():\n'
def make_word_list(string):
    from re import split
    return set(split(r'[ :,()\[\]]|$', string))

class FileLike:
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
        if len(self._string) == 0:
            return 0
        max_offset = len(self.string) -1
        if (offset == 0 and flag == 2) or (offset > max_offset):
            self.cursor = max_offset
        elif 0 <= offset <= max_offset:
            self.cursor = offset
        else:
            breakpoint()

def find_end_of_line(buff):
    offset = buff._string.find('\n', 0, buff.cursor)
    if offset == -1:
        return len(buff._string)
    return buff.cursor + offset

def find_end_of_word(buff):
    places = set()
    if (start := buff.cursor + 2) > len(buff):
        return buff.cursor
    global DELIMS
    for char in DELIMS:
        loc = buff[start:].find(char)
        if loc > -1:
            loc += buff.cursor
            places.add(loc+1)
    if places:
        return min(places)
    return buff.cursor

def find_end_of_WORD(buff):
    start = buff.cursor
    try:
        while buff[start].isspace():
            start += 1
        if (start := buff.cursor + 2) > len(buff):
            return buff.cursor
        sp_offset = buff[start:].find(' ')
        nl_offset = buff[start:].find('\n')
        offset = min( (sp_offset, nl_offset,) )
        if offset == -1:
            return len(buff)
        return start + offset
    except IndexError:
        return buff.cursor

def find_begining_of_line(buff):
    char = ''
    pos = buff.cursor
    if buff.cursor > 0:
        buff.seek(pos - 1)
    else:
        return 0
    while True:
        char = buff.read(1)
        if char == '\n':
            rv = buff.tell()
            buff.seek(pos)
            return rv
        next_pos = buff.tell() - 2
        if next_pos < 0:
            buff.seek(pos)
            return 0
        else:
            buff.seek(next_pos)

def find_first_non_blank_char_in_line(buff):
    pos = buff.tell()
    buff.seek(find_begining_of_line(buff))
    rv = find_next_non_blank_char(buff)
    buff.seek(pos)
    return rv

def find_next_non_blank_char(buff):
    pos = buff.cursor
    while buff._string[pos].isspace():
        pos += 1
    rv = buff.tell() - 1
    buff.seek(pos)
    return rv

def find_normal_k(buff):
    cursor = buff.cursor
    on_col=1
    while (line_start := cursor - on_col ) >= 0:
        if buff[line_start] == '\n':
            break
        else:
            on_col += 1
    else:
        return 0

    previous_line = int(line_start) - 1
    while previous_line >= 0:
        if buff[previous_line] == '\n':
            break
        else:
            previous_line -= 1
    else:
        return 0

    new_cursor = int(previous_line) +1
    while new_cursor <= previous_line + on_col -1:
        if buff[new_cursor] == '\n':
            return new_cursor
        else:
            new_cursor += 1
    return new_cursor


def find_normal_j(buff):
    lin, col = buff.cursor_lin_col
    if lin+1 >= len(buff.lines_offsets):
        return buff.cursor
    next_lin_offset = buff.lines_offsets[lin+1]
    max_offset = next_lin_offset + len(buff.splited_lines[lin+1])
    if next_lin_offset + col > max_offset:
        return max_offset
    return next_lin_offset + col - 1

def find_normal_l(buff):
    if buff[buff.cursor] == '\n':
        return buff.cursor
    elif buff.cursor < len(buff):
        return buff.cursor + 1

def find_normal_h(buff):
    if buff.cursor == 0:
        return 0
    if buff._string[buff.cursor - 1] == '\n':
        return buff.cursor
    return buff.cursor - 1

def find_next_WORD(buff):
    cursor = buff.cursor +1
    try:
        if not buff[cursor].isspace(): 
            while not buff[cursor].isspace(): 
                cursor += 1
        while buff[cursor].isspace(): 
            cursor += 1
        return cursor
    except IndexError:
        return cursor

def find_next_word(buff):
    cursor = buff.cursor +1
    try:
        while not buff[cursor] in DELIMS:
            cursor += 1
        while buff[cursor].isspace(): 
            cursor += 1
        return cursor
    except IndexError:
        return cursor

def find_first_char_of_word(buff):
    if buff.cursor == 0:
        return 0
    elif  buff[buff.cursor - 1].isspace():
        return buff.cursor
    else:
        return buff[:buff.cursor].rfind(' ') + 1

def find_normal_b(buff):
    old_pos = buff.tell()
    word_offset = find_first_char_of_word(buff) 
    if word_offset == old_pos and word_offset != 0:
        buff.seek(old_pos - 1)
        rv = find_first_char_of_word(buff)
        buff.seek(old_pos)
        return rv
    else:
        return word_offset

def find_next_delim(buff):
    global DELIMS
    cursor = buff.cursor
    while buff._string[cursor] in DELIMS:
        if cursor == len(buff) - 1:
            return cursor
        cursor += 1
    while buff._string[cursor] not in DELIMS:
        if cursor == len(buff) - 1:
            return cursor
        cursor +=1
    while buff._string[cursor].isspace():
        if cursor == len(buff) - 1:
            return cursor
        cursor +=1
    return cursor

def find_previous_delim(buff):
    global DELIMS
    cursor = buff.cursor
    while buff._string[cursor] in DELIMS:
        cursor -= 1
    while buff._string[cursor] not in DELIMS:
        if cursor == 0:
            return cursor
        cursor -=1
    return cursor

def inner_word(buff):
    return slice(find_previous_delim(buff),find_next_delim(buff))

def INNER_WORD(buff):
    start = buff.string.rfind(' ', 0, buff.cursor + 1)
    if start == -1:
        start = 0
    else:
        start +=1
    stop = buff._string.find(' ', buff.cursor + 1)
    if stop == -1:
        stop = len(buff.string) - 1
    return slice(start, stop)

def current_line(buff):
    start = find_begining_of_line(buff)
    stop = find_end_of_line(buff)
    if stop < len(buff):
        stop +=1
    return slice(start, stop)

motion = {
    '.':    current_line,
    'b':    find_previous_delim,
    'iw':   inner_word,
    'h':    find_normal_h,
    'j':    find_normal_j,
    'k':    find_normal_k,
    'l':    find_normal_l,
    'w':    find_next_delim,
    'W':    find_next_WORD,
    'G':    lambda buff: len(buff) - 1 ,
    'gg':   lambda buff: 0,
    'cursor': lambda buff: buff.cursor,
    'e':    find_end_of_word,
    'E':    find_end_of_WORD,
    '$':    find_end_of_line,
    '0':    find_begining_of_line,
    '_':    find_first_non_blank_char_in_line,
    }



class Motions(FileLike):
    def __init__(self, cursor=0, init_text='', path=None, **kwargs):
        self.path = path
        self.cursor = cursor
        self._string = init_text
        super().__init__(**kwargs)

    @property
    def string(self):
        return self._string

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
        if not hasattr(self, '_lines_offsets') or \
                        self._lines_offsets_hash != hash(self._string):
            offset = 0
            linesOffsets = list()
            for line in self._string.splitlines(True):
                linesOffsets.append(offset)
                offset += len(line)
            self._lines_offsets_hash = hash(self._string)
            self._lines_offsets = linesOffsets
        return self._lines_offsets

    @property
    def splited_lines(self):
        if not hasattr(self, '_splited_lines') or \
                    self._hash_of_splited_lines != hash(self._string):
            self._splited_lines = list(self._string.splitlines())
            self._hash_of_splited_lines = hash(self._string)
        return self._splited_lines

    @property
    def number_of_lin(self):
        """Number of lines in the buffer"""
        return len(self.lines_offsets)
    def move_cursor(self, offset_str):
        self.cursor = self._get_offset(offset_str)
    
    def __len__(self):
        return len(self._string)

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
                stop = len(self._string)
            return slice(self._get_offset(start), self._get_offset(stop))
        else:
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
                    return len(self._string)
            elif key.startswith('#-'):
                try:
                    entry = self._lines_offsets.index(current_line_start) - int(key[2:])
                    return self._lines_offsets[entry]
                except (IndexError, ValueError):
                    return len(self._string)

            try:
                return self.lines_offsets[int(key[1:])]
            except IndexError:
                return len(self._string)
        return motion[key](self)

    def __delitem__(self, key):
        if isinstance(key, int):
            if key >=0 and key < len(self.string):
                self.string = self._string[0:key] + self._string[key+1:]
            else:
                raise IndexError('Vy Runtime: string index out of range')

        elif isinstance(key, slice):
            if not key.start:
                start = 0
            else:
                start = key.start
            if not key.stop:
                stop = len(self._string)
            else:
                stop = key.stop
            self.string = f'{self._string[:start]}{self._string[stop:]}'
            if key.start < self.cursor <= key.stop:
                self.cursor = key.start

        elif isinstance(key, str):
            key = self._get_range(key)
            return self.__delitem__(key)
        else:
            raise 

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


if __name__ == '__main__':
    test = Motions()
    test._string = '1234 6789\n'
    test.cursor = 0
    assert test['gg:G']     == '1234 6789\n'
    assert test[':G']       == '1234 6789\n'
    assert test['gg:']      == '1234 6789\n'
    assert test['.']        == '1234 6789\n'
    assert test['h']        == '1'
    assert test['j']        == '1'
    assert test['k']        == '1'
    assert test['l']        == '2'
    assert test['cursor']   == '1'
    assert test['cursor:w'] == '1234 '
    assert test['cursor:e'] == '1234'


