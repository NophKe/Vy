from rlcompleter  import Completer 
import readline
from pathlib import Path
from code import InteractiveConsole

name_space = None

class Console(InteractiveConsole):
    def __init__(self, locals=None, filename="<console>", screen=None):
        self.screen = screen
        self.histfile=Path("~/.vym/python_history").expanduser()
        if not self.histfile.exists():
            self.histfile.touch()
        InteractiveConsole.__init__(self, locals, filename)
        readline.parse_and_bind("tab: complete")
        readline.clear_history()
        readline.read_history_file(self.histfile)

    def save_history(self):
        try:
            readline.set_history_length(1000)
            readline.write_history_file(self.histfile)
        except FileNotFoundError:
            pass
        
    def push(self, line):
        rv = super().push(line)
        if not rv:
            self.screen.show(True)
            self.screen.infobar()
        return rv

def loop(editor):
    def new_exit():
        console.resetbuffer()
        raise SystemExit

    global name_space
    if name_space is None:
        print('\tuse :eval in a python source file to use its name_space.')
        name_space = {}
    else:
        print()
        print('\tBuffer correctly evaluated.')
        print()
    name_space['exit'] = new_exit
    readline.set_completer(Completer(name_space).complete)
#
    console = Console(locals= name_space, screen=editor.screen)
    old_screen_minibar_ = editor.screen._minibar_flag
    editor.screen._minibar_flag = editor.screen.number_of_lin // 2

    try:
        console.interact()
    except SystemExit:
        pass

    name_space = None
    console.save_history()
    editor.screen._minibar_flag = old_screen_minibar_

    return 'normal'
