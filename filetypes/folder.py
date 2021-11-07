from pathlib import Path
#from ..behaviour import BaseBehaviour
from .. import keys as k

def DO_open_file(editor):
    file = editor.current_buffer.value[editor.current_buffer.cursor_lin]
    try:
        editor.edit(file)
    except UnicodeDecodeError:
        editor.screen.minibar("Vy ne gère pas l'encodage de ce fichier")
    except PermissionError:
        editor.screen.minibar(f"Not enough right to read {file}")
    return 'normal'

def DO_edit_next_unsaved_or_enew(editor):
    for buff in editor.cache:
        if buff.unsaved:
            editor.edit(buff)
            return 'normal'
    editor.edit(None)
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

class Folder: #(BaseBehaviour):
    unsaved = False
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

    def interract(self, editor):
        while True:
            editor.show_screen(True)
            key = editor.read_stdin()
            editor.screen.infobar(f' ( Processing Command: {k._escape(key)} )')
            if key == k.down or key == 'j':
                self.go_down()
            elif key == k.up or key == 'k':
                self.go_up()
            elif key == '\r':
                return DO_open_file(editor)
            elif key == '\x1b':
                return DO_edit_next_unsaved_or_enew(editor)


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

    motion_cmd = {
        k.down: 'j',
        'j': lambda curbuf: curbuf.go_down(),
        k.up: 'k',
        'k': lambda curbuf: curbuf.go_up(),
        '\r': DO_open_file,
        }


