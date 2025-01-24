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
        editor.screen.minibar('File opened externally.')
    else:
        return 'normal'

def DO_delete_file(editor, *args, **kwargs):
    curbuf = editor.current_buffer
    path = curbuf._values[curbuf.current_line_idx]
    path: Path
    editor.confirm(f'deleting {path}')
    path.unlink()
    curbuf._string = ''
    curbuf._splited_lines.clear()
    curbuf.string
    return 'normal'

class Folder(BaseFile):
    actions = { 
        k.CR: DO_open_file, 
        ':delete_this_file': DO_delete_file,
        }
    unsaved = False
    modifiable = False
    
    @property
    def string(self):
        from pathlib import Path
            
        if not self._string:
            assert self.path
            
            value = []
            value.extend(sorted(x for x in self.path.iterdir() if x.is_dir()     and not x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if x.is_dir()     and     x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if not x.is_dir() and not x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if not x.is_dir() and     x.name.startswith('.')))

            self._values = [self.path.parent.resolve()] + value
            
            cwd = self.path.cwd().resolve()
            pretty = []
            
            for pth in self._values:
                if pth.is_relative_to(cwd) and pth != cwd:
                    ret = str(pth.relative_to(cwd))
                else:
                    ret = str(pth.resolve())
                if pth.is_dir():
                    ret += '/'
                pretty.append(ret)
            
            self._string = '\n'.join(iter(pretty))
            self._lenght = len(self._string)
        return self._string

    @string.setter
    def string(self, value):
        return

    def get_raw_line(self, index):
        retval = self.splited_lines[index].removesuffix('\n') + '\x1b[22m'
        from vy.global_config import BG_COLOR
        if index == 0:
            return '\x1b[1;33;44m' + retval + BG_COLOR
        elif index == self.current_line_idx:
            return '\x1b[1;37;42m' + retval + BG_COLOR
        else:
            return retval

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
