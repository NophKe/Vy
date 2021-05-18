def find_end_of_line(buff):
    offset = buff[buff.cursor:].find('\n')
    if offset == -1:
        return len(buff)
    return buff.cursor + offset

def find_end_of_word(buff):
    pos = buff.tell()
    buff.read(1)
    while buff.read(1).isspace():
        pass
    buff.seek(buff.tell() - 1)
    while not buff.read(1).isspace():
        pass
    rv = buff.tell() - 2
    buff.seek(pos)
    return rv

def find_begining_of_line(buff):
    char = ''
    pos = buff.tell()
    if pos > 0:
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
    pos = buff.tell()
    while buff.read(1).isspace():
        pass
    rv = buff.tell() - 1
    buff.seek(pos)
    return rv

def find_normal_k(buff):
    cursor = buff.tell()
    on_col=1
    line_start = buff.tell()
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
    next_line = find_end_of_line(buff) + 1
    on_col = buff.cursor - find_begining_of_line(buff)
    for idx in range(next_line, len(buff)):
        if idx == next_line + on_col:
            return idx
        if buff[idx] == '\n':
            return idx
    return len(buff)

def find_normal_l(buff):
    if buff[buff.cursor] == '\n':
        return buff.cursor
    elif buff.cursor < len(buff):
        return buff.cursor + 1

def find_normal_h(buff):
    old_pos = buff.tell()
    pos = old_pos - 1
    if pos < 0:
        return 0
    buff.seek(pos)
    if buff.read(1) == '\n':
        return old_pos
    else:
        return pos

def find_next_word(buff):
    pos = buff.tell()
    next_char = buff.read(1)
    if not next_char:
        buff.seek(pos)
        return len(buff)
    if next_char.isspace(): 
        while buff.read(1).isspace():
            continue
        else:
            rv = buff.tell() - 1
            buff.seek(pos)
            return rv
    else:
        rv = find_next_word(buff)
        buff.seek(pos)
        return rv

def find_first_char_of_word(buff):
    if buff.cursor == 0:
        return 0
    elif  buff[buff.cursor - 1].isspace():
        return buff.cursor
    else:
        return buff[':cursor'].rfind(' ') + 1

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

def inner_word(buff):
    start = buff[:buff.cursor].rfind(' ')
    if start == -1:
        start = 0
    else:
        start += 1

    stop = buff[:buff.cursor].find(' ')
    if stop == -1:
        stop = len(buff.string)
    else:
        stop += buff.cursor

    return slice(start, stop)

def current_line(buff):
    start = find_begining_of_line(buff)
    stop = find_end_of_line(buff)
    if stop < len(buff):
        stop +=1
    return slice(start, stop)

motion = {
    '.':    current_line,
    'b':    find_normal_b,
    'iw':   inner_word,
    'h':    find_normal_h,
    'j':    find_normal_j,
    'k':    find_normal_k,
    'l':    find_normal_l,
    'w':    find_next_word,
    'G':    lambda buff: len(buff),
    'gg':   lambda buff: 0,
    'cursor': lambda buff: buff.cursor,
    'e':    find_end_of_word,
    '$':    find_end_of_line,
    '0':    find_begining_of_line,
    '_':    find_first_non_blank_char_in_line,
    }



class Motions():
    def move_cursor(self, offset_str):
        return self.seek(self._get_offset(offset_str))
    
    def __len__(self):
        return len(self.string)

    def __getitem__(self, key):
        if isinstance(key, str):
            key = self._get_range(key)
        return self.string.__getitem__(key)

    def _get_range(self,key):
        if ':' in key:
            start, stop = key.split(':', maxsplit=1)
            start = start.lstrip(':')
            stop = stop.rstrip(':')
            if not start:
                start = 0
            if not stop:
                stop = len(self.string)
            return slice(self._get_offset(start), self._get_offset(stop))
        else:
            return self._get_offset(key)

    def _get_offset(self, key):
        if isinstance(key, int):
            return key
        elif isinstance(key, str):
            return motion[key](self)

    def __delitem__(self, key):
        if isinstance(key, int):
            if key >=0 and key < len(self.string):
                self.string = self._string[0:key] + self._string[key+1:]
            else:
                raise IndexError('string index out of range')

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

        elif isinstance(key, str):
            key = self._get_range(key)
            return self.__delitem__(key)

    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = self._get_range(key)
        if isinstance(key, slice):
            start = key.start
            stop = key.stop
        if isinstance(key, int):
            start = key
            stop = start + 1
        self.string = f'{self._string[:start]}{value}{self._string[stop:]}'

    def insert(self, text):
        self.string = f'{self._string[:self.cursor]}{text}{self._string[self.cursor:]}'
        self.cursor += len(text)
