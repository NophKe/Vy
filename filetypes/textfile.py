from pathlib import Path
from .filelike import FileLike
from .motions import Motions
from .syntax import view
from ..behaviour import WritableText

class TextFile(Motions, FileLike, view, WritableText):
    def __init__(self, path=None, cursor=0):
        self._no_undoing = False
        self.redo_list = list()
        self.undo_list = list()
        self.cursor = cursor
        self.path = path
        if self.path and self.path.exists():
            self._string = self.path.read_text()
        else:
            self._string = '\n'
        super().__init__()

    def __repr__(self):
        return f"writeable buffer: {self.path.name if self.path else 'undound to file system'}"

    def start_undo_record(self):
        self._no_undoing = False
        self.set_undo_point()
    
    def stop_undo_record(self):
        if self._no_undoing:
            return
        self.set_undo_point()
        self._no_undoing = True

    def set_undo_point(self):
        if self._no_undoing:
            return
        actual_txt, actual_cur = self._string, self.cursor
        actual_off = self.lines_offsets
        act_lex = self.lexed_lines

        if not self.undo_list:
            self.undo_list.append((actual_txt, actual_cur, actual_off, act_lex))
            return
        last_txt, _x, _y, _z= self.undo_list[-1]
        if actual_txt != last_txt:
            self.undo_list.append((actual_txt, actual_cur, actual_off, act_lex))

    def undo(self):
        if not self.undo_list:
            return
        txt, pos, off, lex = self.undo_list.pop()
        self.redo_list.append((self._string, self.cursor,
                                self.lines_offsets, self.lexed_lines))
        self._string = txt
        self.cursor = pos
        self._lines_offsets = off
        self._lexed_lines = lex
        self._lines_offsets_hash = self._lexed_hash = txt.__hash__()
    
    def redo(self):
        if not self.redo_list:
            return
        txt, pos, off, lex = self.redo_list.pop()
        self.undo_list.append((txt, pos, off, lex))
        self._string = txt
        self.cursor = pos
        self._lines_offsets = off
        self._lexed_lines = lex
        self._lines_offsets_hash = self._lexed_hash = txt.__hash__()

    def save(self):
        assert self.path is not None
        self.path.write_text(self.getvalue())

    def save_as(self, new_path=None, override=False):
        assert isinstance(new_path, (str, Path))
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
        elif self.path.read_text() != self.string:
            return True
        return False

    @property
    def CURSOR_lin_col(self):
        string = self._string
        cursor = self.cursor
        lin = string[:cursor].count('\n')
        col = cursor - string[:cursor].rfind('\n')
        if col == -1:
            col = len(self._string)
        return (lin, col)
    
    @property
    def cursor_lin_col(self):
        lin, off = self.cursor_lin_off
        col = self.cursor - off + 1
        return lin, col

    @property
    def cursor_lin_off(self):
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
    def number_of_lin(self):
        return len(self.lines_offsets)

    def suppr(self):
        string = self._string
        cur = self.cursor
        self.string  = f'{string[:cur]}{string[cur + 1:]}'

    def backspace(self):
        if self.cursor > 0:
            self.cursor -= 1
            self.suppr() 

    def insert(self, text):
        string = self._string
        cur = self.cursor
        self.string = f'{string[:cur]}{text}{string[cur:]}'
        self.cursor += len(text)

    def print_yourself(buff):
        from os import get_terminal_size
        max_col, max_lin = get_terminal_size()
        for x in buff.gen_window(1, max_col +1 , 0, max_lin - 1):
            print(x, end='\r')
