from vy import keys as k
from pathlib import Path
from vy.filetypes.basefile import BaseFile

def DO_open_file(editor):
    curbuf = editor.current_buffer
    path = curbuf._values[curbuf.current_line_idx]
    try:
        editor.edit(path)
    except:
        import subprocess
        subprocess.call(["xdg-open", path])
#        from os import startfile
#        startfile(path)
        editor.screen.minibar('File opened externally.')
    else:
        return 'normal'

class Folder(BaseFile):
    actions = { k.CR: DO_open_file, }
    unsaved = False
    modifiable = False
    
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
#            pretty  = [ val for val in value ]
            pretty  = [ val.relative_to(cwd,walk_up=True) for val in value ]
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

    @property    
    def footer(self):
        return str(self.path.resolve())
