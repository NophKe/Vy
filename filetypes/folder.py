from pathlib import Path
from ..behaviour import BaseBehaviour
from .. import keys as k

def DO_open_file(ed, cmd):
    file = ed.current_buffer.value[ed.current_buffer.cursor_lin]
    try:
        ed.edit(file)
    except UnicodeDecodeError:
        ed.warning("Vy ne gère pas l'encodage de ce fichier")
    except PermissionError:
        ed.warning(f"Not enough right to read {file}")
    return 'normal'

def format_lines(max_col, text, cursor_lin, cur_or_par_dir):
    retval = '\x1b[00;90;40m'
    if cur_or_par_dir: #current or parent dir (., ..)
        retval += '\x1b[00;25;35m'
    if cursor_lin:
        retval += '\x1b[7m'
    on_col = 0
    for on_col, char in enumerate(text):
        if on_col ==  max_col -1:
            retval += '\x1b[0m'
            return retval
        retval += char
    retval += (' ' * (max_col - on_col - 1))
    return retval

class Folder(BaseBehaviour):
    def gen_window(self, max_col, min_lin, max_lin):
        for item in range(min_lin, max_lin+1):
            cur_or_par_dir = bool(item == 1 or item == 0)
            cursor = bool(item == self.cursor_lin)
            try:
                yield format_lines(max_col, str(self.value[item]), cursor, cur_or_par_dir)
            except IndexError:
                yield format_lines(max_col, ' ...', False, False)
        while True:
            yield format_lines(max_col, ' ...', False, False)

    def __init__(self, path):
        try:
            self.path = path.relative_to(Path().cwd().resolve())
        except ValueError:
            self.path = path
        self.cursor_lin = 0
        self.value = sorted([self.path.resolve(), (self.path/'..').resolve()])
        self.value.extend(x for x in self.path.iterdir() if not x.name.startswith('.') )

    def go_down(self):
        if self.cursor_lin < len(self.value) -1:
            self.cursor_lin +=1

    def go_up(self):
        if self.cursor_lin > 0:
            self.cursor_lin -= 1

    @property
    def cursor_lin_col(self):
        return (self.cursor_lin, 1)

    stand_alone_commands = {
        k.down: 'j',
        'j': lambda ed, cmd: ed.current_buffer.go_down(),
        k.up: 'k',
        'k': lambda ed, cmd: ed.current_buffer.go_up(),
        '\r': DO_open_file,
        }
    full_commands = {}
    motion_commands = {}


