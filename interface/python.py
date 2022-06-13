from ..global_config import USER_DIR
from rlcompleter  import Completer 
import readline
from pathlib import Path
from code import InteractiveConsole as Console

from vy.interface.helpers import CommandCompleter as VyCompleter

local_completer = VyCompleter('python_history')
name_space = None

#class Console(InteractiveConsole):
    #def __init__(self, locals=None, filename="<console>", editor=None):
        #self.editor = editor
        #self.histfile = USER_DIR / 'python_history'
        #if not self.histfile.exists():
            #self.histfile.touch()
        #InteractiveConsole.__init__(self, locals, filename)
        #return

    #def raw_input(self, prompt=''):
        #return self.editor.read_stdin_line(prompt)
    
    #def save_history(self):
            #pass
        
    #def push(self, line):
        #rv = super().push(line)
        #if not rv:
#
            ##self.editor.show_screen(True)
            ##self.screen.infobar()
        #return rv

def loop(editor):
    try:
        editor.stop_async_io()
        global name_space
        if name_space is None:
            print('\tuse :eval in a python source file to use its name_space.')
            name_space = {}
        else:
            print()
            print('\tBuffer correctly evaluated.')
            print()

        console = Console(locals=name_space)#, editor=editor)
        
        try:
            with local_completer:
                readline.set_completer(Completer(name_space).complete)
                console.interact()
        except SystemExit:
            pass

        name_space = None
        #console.save_history()
        return 'normal'
    finally:
        editor.start_async_io()
