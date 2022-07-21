from .. import keys as k
from pathlib import Path
from .basefile import BaseFile

def DO_open_file(editor):
    file = editor.current_buffer.splited_lines[editor.current_buffer.cursor_line]
    editor.edit(file)
    return 'normal'

class Folder(BaseFile):
    motion_commands = { }
    actions = { k.CR: DO_open_file, }
    unsaved = False
    modifiable = False

    @property
    def string(self):
        if self._string:
            return self._string
        cwd = Path().cwd().resolve()
        browsing  = self.path.resolve()
        value =[ browsing, browsing.parent.resolve() ]
        value.extend(sorted(x.relative_to(cwd) for x in self.path.iterdir() if x.is_dir()))
        value.extend(sorted(x.relative_to(cwd) for x in self.path.iterdir() if not x.name.startswith('.') and not x.is_dir()))
        value.extend(sorted(x.relative_to(cwd) for x in self.path.iterdir() if x.name.startswith('.') and not x.is_dir()))
        self._string = '\n'.join(str(item) if not item.is_dir() else str(item) + '/' for item in value )
        return self._string

    @string.setter
    def string(self, value):
        return

    def get_raw_screen(self, min_lin, max_lin):
        rv = list()
        for index in range(min_lin, max_lin):
            retval = ''
            if index == 1 or index == 0: #current or parent dir (., ..)
                retval = '\x1b[00;25;35m'
            if index == self.cursor_line:
                retval += '\x1b[2m'
            try:
                retval += self.splited_lines[index] + '\x1b[0m' 
            except IndexError:
                retval = None
            rv.append(retval)
        lin, col = self.cursor_lin_col
        return lin, col, rv 
