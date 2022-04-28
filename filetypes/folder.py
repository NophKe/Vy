from .. import keys as k
from pathlib import Path
from .basefile import BaseFile

def DO_open_file(editor):
    file = editor.current_buffer.value[editor.current_buffer.cursor_line]
    try:
        editor.edit(file)
    except UnicodeDecodeError:
        editor.screen.minibar("Vy ne gère pas l'encodage de ce fichier")
    except PermissionError:
        editor.screen.minibar(f"Not enough right to read {file}")
    return 'normal'

class Folder(BaseFile):
    motion_commands = { }
    actions = {'\r': DO_open_file,
               k.C_J: DO_open_file,
        }
    unsaved = False

    @property
    def string(self):
        value =[ self.path.resolve(),
                (self.path/'..').resolve() ]
        value.extend(sorted(x for x in self.path.iterdir() if not x.name.startswith('.') ))
        return '\n'.join(str(line) for line in value)

    @string.setter
    def string(self, value):
        return

    def get_lexed_line(self, index):
        retval = ''
        if index == 1 or index == 0: #current or parent dir (., ..)
            retval = '\x1b[00;25;35m'
        if index == self.cursor_line:
            retval += '\x1b[2m'
        retval += self.splited_lines[index] + '\x1b[0m' 
        return retval 

