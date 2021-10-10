from .motions import Motions

class view(Motions):
    def __init__(self, set_wrap=False, set_tabsize=4, **kwargs):
        self.set_wrap = set_wrap
        self.set_tabsize = set_tabsize
        super().__init__(**kwargs)

    def gen_window(self, max_col, lin_shift, max_lin):
        lin, col = self.cursor_lin_col
        splited_lines = self.splited_lines
        for index in range(lin_shift, max_lin):
            try:
                line = splited_lines[index]
            except IndexError:
                break
            if lin == index:
                if col < len(line):
                    line = line[:col] + '\x1b7\x1b[7;5m' + line[col] + '\x1b[25;27m' + line[col+1:]
                else:
                    line = line[:col] + '\x1b7\x1b[7;5m \x1b[25;27m'
            yield line.expandtabs(tabsize=self.set_tabsize).ljust(max_col, ' ')
