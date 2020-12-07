from pathlib import Path
from .descriptors import VyString, VyPath
from .filelike import FileLike
#from .pygments import Printer
from .motions import Motions

class TextFile(Motions, FileLike):
    string = VyString()
    path = VyPath()

    def __init__(self, path=None, cursor=0):
        self.lexer = None
        self.tab_size = 4
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
        #breakpoint()
        if self.path is None or not self.path.exists():
            if self.string != '\n':
                return True
        elif self.path.read_text() != self.string:
            return True
        return False

    @property
    def cursor_lin_col(self):
        offset = 0
        lin = 0
        col = 0
        for line_number, line in enumerate(self.string.splitlines(True), start=1):
            offset += len(line)
            if offset >= self.cursor:
                col = int(len(line) - (offset - self.cursor))
                lin = int(line_number)
                break
        return (lin, col)

    @property
    def number_of_lin(self):
        return self.string.count('\n')

    def suppr(self):
        self.string  = self.string[:self.cursor] + self.string[self.cursor + 1 :]

    def backspace(self):
        if self.cursor > 0:
            self.cursor -= 1
            self.suppr() 

    def insert(self, text):
        string = self.string
        cur = self.cursor
        self.string = f'{string[:cur]}{text}{string[cur:]}'
        self.cursor += len(text)


def print_buffer(buff):
    from os import get_terminal_size
    max_col, max_lin = get_terminal_size()

    for x in buff.gen_window(1, max_col +1 , 0, max_lin - 1):
        print(x, end='\r')


if __name__ == '__main__':
    buff = TextFile()
    buff.insert('''1
2
3
4444|4444|4444|4444|
5555|5555|5555|5555|
6   5   10   15   20 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
7  x|xxxx|xxxx|xxxx|xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
8   tres longue ligne __________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
9   |xxxx|xxxx|xxxx|xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
10
____|____|ONZE|__ _|_ __ _  ONZE     ____ __ _ _ __
12  is ful of trailing spaces                                                                                                                                                                                                           

here is 14:  last one (13) was empty    xxxxxxxxxxx
xxxx|xxxx|xxxx|xxxx|xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
next one (15) start with three tabs
            xxxx|xxxx|xxxx|xxxx|xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
xxxx|xxxx|xxxx|xxxx|xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
next is only tabs
                                                    
xxxx|xxxx|xxxx

|xxxx|xxxx

xxxxxxxxxxxxxxxxxxxxxxxxxxx

xxxx|xxxx|xx

xx|xxxx|xxxx

xxxxxx

xxxxxxxxxxxxxxxxxxxxx

xxxx

|xxxx|xxxx|xxx       xxxxxxxxxxxxxxxxxxx''')


    print_buffer(buff)


