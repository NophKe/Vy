from .. import keys as k
from pathlib import Path
#from .basefile import BaseFile
from vy.filetypes.textfile import TextFile

def DO_open_file(editor):
    curbuf = editor.current_buffer
    file = curbuf._values[curbuf.current_line_idx]
    editor.edit(file)
    return 'normal'

class Folder(TextFile):
    motion_commands = { }
    actions = { k.CR: DO_open_file, }
    unsaved = False
    modifiable = False
    
    @property
    def _lexed_lines(self):
        return self._splited_lines

    @property
    def _string(self):
        try:
            return self._text
        except AttributeError:
            cwd = Path().cwd().resolve()
            browsing  = self.path.resolve()
            while not browsing.is_relative_to(cwd):
                cwd = cwd.parent
            value =[ browsing.parent.resolve(), browsing ]
            value.extend(sorted(x for x in self.path.iterdir() if x.is_dir() and not x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if not x.name.startswith('.') and not x.is_dir()))
            value.extend(sorted(x for x in self.path.iterdir() if x.is_dir() and x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if x.name.startswith('.') and not x.is_dir()))

            self._values = [ val.resolve() for val in value ]
            pretty  = [val for val in value ]
            self._text = '\n'.join(str(item) if not item.is_dir() else str(item) + '/' for item in pretty )
        return self._text

    @_string.setter
    def _string(self, value):
        return

    def get_raw_screen(self, min_lin, max_lin):
        rv = list()
        for index in range(min_lin, max_lin):
            retval = ''
            if index == 1 or index == 0: #current or parent dir (., ..)
                retval = '\x1b[00;25;35;1m'
            if index == self.current_line_idx:
                retval += '\x1b[2m'
            try:
                retval += self.splited_lines[index].removesuffix('\n') + '\x1b[0m' 
            except IndexError:
                retval = None
            rv.append(retval)
        lin, col = self.cursor_lin_col
        return lin, col, rv 
