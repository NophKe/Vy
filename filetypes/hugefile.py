#from ..behaviour import ReadOnlyText
from .textfile import TextFile

class HugeFile(TextFile):
    set_tab_size = 4
    def gen_window(buff, max_col, lin_shift, max_lin):
        lin, col = buff.cursor_lin_col
        for index in range(lin_shift, max_lin):
            line = buff.splited_lines[index]
            if lin == index:
                if col < len(line):
                    line = line[:col] + '\x1b7\x1b[7;5m' + line[col] + '\x1b[25;27m' + line[col+1:]
                else:
                    line = line[:col] + '\x1b7\x1b[7;5m \x1b[25;27m'
            yield line.expandtabs(tabsize=buff.set_tab_size).ljust(max_col, ' ')
    @property
    def splited_lines(self):
        if not hasattr(self, '_splited_lines') or \
                    self._hash_of_splited_lines != hash(self._string):
            self._splited_lines = list(self._string.splitlines())
            self._hash_of_splited_lines = hash(self._string)
        return self._splited_lines

    
