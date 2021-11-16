from rlcompleter  import Completer 
import readline
from pathlib import Path
from code import InteractiveConsole



name_space = None

class Console(InteractiveConsole):
    def __init__(self, locals=None, filename="<console>", editor=None):
        self.editor = editor
        self.histfile = Path("~/.vym/python_history").expanduser()
        #self.session = Path("~/.vym/python_history").expanduser()
        #if not self.session.exists():
            #self.session.touch()
        if not self.histfile.exists():
            self.histfile.touch()
        InteractiveConsole.__init__(self, locals, filename)
        readline.parse_and_bind("tab: complete")
        readline.clear_history()
        readline.read_history_file(self.histfile)
    
    #def raw_input(self, prompt):
        #rv = input(prompt)
        #self.session.write_line(rv)
        #return rv


    def save_history(self):
        try:
            readline.set_history_length(1000)
            readline.write_history_file(self.histfile)
        except FileNotFoundError:
            pass
        
    def push(self, line):
        rv = super().push(line)
        if not rv:
            self.editor.show_screen(True)
            #self.screen.infobar()
        return rv

def loop(editor):
#   def new_exit():
#       console.resetbuffer()
#       raise SystemExit

    global name_space
    if name_space is None:
        print('\tuse :eval in a python source file to use its name_space.')
        name_space = {}
    else:
        print()
        print('\tBuffer correctly evaluated.')
        print()
    readline.set_completer(Completer(name_space).complete)
#
    console = Console(locals= name_space, editor=editor)

#   def new_exit(console):
#       console.resetbuffer()
#       raise SystemExit

#   name_space['exit'] = lambda: new_exit(console)
    
    old_screen_minibar_ = editor.screen._minibar_flag
    editor.screen._minibar_flag = editor.screen.number_of_lin // 2
    editor.screen.minibar('')

    try:
        console.interact()
    except SystemExit:
        pass

    name_space = None
    console.save_history()
    editor.screen._minibar_flag = old_screen_minibar_

    return 'normal'
