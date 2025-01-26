from vy import keys as k
from pathlib import Path
from vy.filetypes.basefile import BaseFile

def DO_open_file(editor):
    curbuf = editor.current_buffer
    path = curbuf._values[curbuf.current_line_idx]
    try:
        editor.cache[path]
    except PermissionError as exc:
        editor.screen.minibar(str(exc))
    except UnicodeDecodeError:
        editor.confirm('try to open this file externally ?')
        import subprocess
        import threading
        threading.Thread(target= lambda:subprocess.call(["xdg-open", path]),
                         daemon=True,
                        ).start()
        editor.screen.minibar('File opened externally.')
    else:
        editor.edit(path)
    return 'normal'

def DO_delete_file(editor, *args, **kwargs):
    curbuf = editor.current_buffer
    path = curbuf._values[curbuf.current_line_idx]
    path: Path
    editor.confirm(f'delete {path} ?')
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
            browsing = self.path
            while browsing != Path('/'):
                value.append(browsing)
                browsing = browsing.parent
            else:
                value.append(browsing)
            
            value.reverse()
            
            value.extend(sorted(x for x in self.path.iterdir() if x.is_dir()     and not x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if x.is_dir()     and     x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if not x.is_dir() and not x.name.startswith('.')))
            value.extend(sorted(x for x in self.path.iterdir() if not x.is_dir() and     x.name.startswith('.')))

            self._values = value
            
            cwd = self.path.cwd().resolve()
            pretty = []
            
            for pth in self._values:
                if pth.is_relative_to(cwd) and pth != cwd:
                    ret = str(pth.relative_to(cwd))
                else:
                    ret = str(pth.resolve())
                    
                if pth.is_dir():
                    ret += '/'
                    
                if ret.endswith('/') and not ret.startswith('/'):
                    ret = '\x1b[1m' + ret + '\x1b[22m'
                else:
                    ret = '\x1b[3m' + ret + '\x1b[23m'
                pretty.append(ret)
            
            self._string = '\n'.join(iter(pretty))
            self._lenght = len(self._string)
        return self._string


    def get_raw_line(self, index):
        retval = self.splited_lines[index].removesuffix('\n') + '\x1b[22m'
        from vy.global_config import BG_COLOR
        if index == self.current_line_idx:
            return '\x1b[45m' + retval + BG_COLOR
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


    @string.setter
    def string(self, value):
        return
