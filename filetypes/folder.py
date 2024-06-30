from .. import keys as k
from pathlib import Path
from .basefile import BaseFile
from vy.filetypes.textfile import TextFile

def DO_open_file(editor):
    curbuf = editor.current_buffer
    editor.edit(curbuf._values[curbuf.current_line_idx])
    return 'normal'

class Folder(BaseFile):
    actions = { k.CR: DO_open_file, }
    unsaved = False
    
    @property
    def string(self):
        if not self._string:
            cwd = Path().cwd().resolve()
            browsing  = self.path.resolve()
            while not browsing.is_relative_to(cwd):
                cwd = cwd.parent
            value = [browsing.parent.resolve()]

            value.extend(sorted(x for x in self.path.iterdir() if x.is_dir()     and not x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if x.is_dir()     and     x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if not x.is_dir() and not x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if not x.is_dir() and     x.name.startswith('.')))

            self._values = [ val.resolve() for val in value ]
            pretty  = [ val for val in value ]
            self._string = '\n'.join(str(item) if not item.is_dir() else str(item) + '/' for item in pretty )
            self._lenght = len(self._string)
        return self._string

    @string.setter
    def string(self, value):
        return

    def get_raw_line(self, index):
        return self.splited_lines[index].removesuffix('\n') + '\x1b[22m'

    def get_raw_screen(self, min_lin, max_lin):
        rv = []
        for index in range(min_lin, max_lin):
            try:
                line = self.get_raw_line(index) 
            except IndexError:
                line = None
            finally:
                rv.append(line)
        else:
            lin, col = self.cursor_lin_col
            return lin, col, rv 
