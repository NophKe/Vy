from .motions import Motions
from .filelike import FileLike
from .motions import Motions
from .syntax import view
from ..behaviour import ReadOnlyText 

class ReadOnlyTextFile(Motions, view, ReadOnlyText):
    
    @property
    def hash(self):
        self._old_hash = hash(self._string)
        return self._old_hash
    
    def __init__(self, path, cursor=0):
        self.cursor = cursor
        self.path = path
        if self.path:
            try:
                self._string = self.path.read_text()
            except FileNotFoundError:
                self._string = '\n'
        else:
            self._string = '\n'
        self._old_hash = hash(self._string)
        self._old_cursor = self.cursor
        self._old_lin_col = None
        super().__init__()

    @property
    def cursor_lin_col(self):
        string = self._string
        if (hash(string) == self._old_hash 
                    and self._old_cursor == self.cursor
                    and self._old_lin_col):
            return self._old_lin_col
        
        cursor = self.cursor
        lin = string[:cursor].count('\n')
        col = cursor - string[:cursor].rfind('\n')
        if col == -1:
            col = len(self._string)
        self._old_lin_col = (lin, col)
        self._old_cursor = cursor
        return self._old_lin_col

    @property
    def number_of_lin(self):
        return self._string.count('\n')

    def getvalue(self):
        return self._string

    def read(self, nchar= -1):
        if self.cursor == len(self._string):
            return ''
        if nchar == -1:
            rv = self.string[self.cursor:]
            self.cursor = len(self._string)
        else:
            rv = self._string[self.cursor:(self.cursor + nchar)]
            self.cursor = self.cursor + nchar
        return rv

    def tell(self):
        return self.cursor

    def seek(self,offset=0, flag=0):
        assert isinstance(offset, int)
        assert isinstance(flag, int)
        if len(self.string) == 0:
            return 0
        max_offset = len(self.string) 
        if (offset == 0 and flag == 2) or (offset > max_offset):
            self.cursor = max_offset
        elif 0 <= offset <= max_offset:
            self.cursor = offset
        else:
            breakpoint() 
