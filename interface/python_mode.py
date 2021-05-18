import readline
import code
import __main__
import os
from pathlib import Path

class Console(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>", screen=object):
        self.screen = screen
        histfile=Path("~/.vy/python_history").expanduser()
        self.histfile = histfile
        code.InteractiveConsole.__init__(self, locals, filename)
        self.init_history(histfile)

    def init_history(self, histfile):
        readline.parse_and_bind("tab: complete")
        if hasattr(readline, "read_history_file"):
            try:
                readline.read_history_file(histfile)
            except FileNotFoundError:
                pass

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
    #readline.parse_and_bind("tab: complete")
    
    print('\tYou are now in a python repl.')
    print('\tYou can access Vy by the «Editor» variable')
    print('\trisk and profit...')
    print()
    print('\tnote that you are back in __main__ no matter what this means!')
    print()

    console = Console(locals= __main__.__dict__, screen= editor.screen)

    def DO_not_try(*args):
        print('\tyou cannot interract with the editor stacking call to:')
        print('\tEditor()')
        print('\tEditor.interface()')
        print()
        print('\tuse ^D or exit() to resume to the editor.')
    
    def new_exit():
        console.resetbuffer()
        raise SystemExit

    #old_interface = editor.interface
    #old_cmdloop = editor.cmdloop
    old_screen_minibar_ = editor.screen._minibar_flag

    #editor.interface = DO_not_try
    #editor.cmdloop = DO_not_try
    editor.screen._minibar_flag = editor.screen.number_of_lin // 2


    __main__.exit = new_exit
    try:
        console.interact()
    except SystemExit:
        pass
    finally:
        console.save_history()
        

    del __main__.exit
    #editor.cmdloop = old_cmdloop
    #editor.interface = old_interface
    editor.screen._minibar_flag = old_screen_minibar_

    return 'normal'
