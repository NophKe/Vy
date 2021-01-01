from pathlib import Path
from .descriptors import VyString, VyPath
from .filelike import FileLike
from .motions import Motions

class TextFile(Motions, FileLike):
    string = VyString()
    path = VyPath()

    def __init__(self, path=None, cursor=0):
        self._no_undoing = False
        self.set_wrap = False
        self.set_tabsize = 4
        self.lexer = None
        self.redo_list = list()
        self.undo_list = list()
        self.cursor = cursor
        self.path = path
        if self.path:
            try:
                self._string = self.path.read_text()
            except FileNotFoundError:
                self._string = '\n'
        else:
            self._string = '\n'
            # this ensures the file ends with new_line (standard)
            # and avoids problem of where to draw a cursor on an
            # empty text.
    def start_undo_record(self):
        self._no_undoing = False
        self.set_undo_point()
    
    def stop_undo_record(self):
        if self._no_undoing:
            return
        self.set_undo_point()
        self._no_undoing = True

    def set_undo_point(self):
            actual = (self._string, self.cursor)
            if not self.undo_list:
                self.undo_list.append(actual)
                return
            last = self.undo_list[-1]
            if actual != last:
                self.undo_list.append(actual)

    def undo(self):
        if not self.undo_list:
            return
        txt, pos = self.undo_list.pop()
        self.redo_list.append((self._string,self.tell()))
        self._string = txt
        self.cursor = pos
    
    def redo(self):
        if not self.redo_list:
            return
        txt, pos = self.redo_list.pop()
        self.undo_list.append((txt, pos))
        self._string = txt
        self.cursor = pos

    def save(self):
        assert self.path is not None
        self.path.write_text(self.getvalue())


    def save_as(self, new_path, override=False):
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
                    self.path = new_path.resolve()
                    self.save()
                else:
                    raise FileExistsError('Add ! in interface or override=True in *kwargs ....')
    @property
    def unsaved(self):
        if self.path is None or not self.path.exists():
            if self.string != '\n':
                return True
        elif self.path.read_text() != self.string:
            return True
        return False


    @property
    def CURSOR_LIN_COL(self):
        offset = 0
        lin = 0
        col = 0
        for line_number, line in enumerate(self._string.splitlines(True), start=1):
            offset += len(line)
            if offset >= self.cursor:
                col = int(len(line) - (offset - self.cursor))
                lin = int(line_number)
                break
        return (lin, col)

    @property
    def cursor_lin_col(self):
        string = self._string
        cursor = self.cursor
        lin = string[:cursor].count('\n')
        col = cursor - string[:cursor].rfind('\n')
        if col == -1:
            col = len(self._string)
        return (lin, col)

    @property
    def number_of_lin(self):
        return self.string.count('\n')

    def suppr(self):
        string = self._string
        cursor = self.cursor
        self.string  = string[:cursor] + string[cursor + 1 :]

    def backspace(self):
        if self.cursor > 0:
            self.cursor -= 1
            self.suppr() 

    def insert(self, text):
        string = self._string
        cur = self.cursor
        self.string = f'{string[:cur]}{text}{string[cur:]}'
        self.cursor += len(text)


def print_buffer(buff):
    from os import get_terminal_size
    max_col, max_lin = get_terminal_size()
    for x in buff.gen_window(1, max_col +1 , 0, max_lin - 1):
        print(x, end='\r')
