from code import InteractiveConsole
from vy.interface.helpers import Completer

def loop(editor):
    class Console(InteractiveConsole):
        def write(self, text):
            text = text.splitlines()
            editor.screen.minibar(*text)
            
    readline = Completer('ex_history', '>>> ', editor,)
    locals_dict = {'vy': editor}
    console = Console(locals=locals_dict)

    lines = list()
    line = readline()

    while console.push(line):
        editor.screen.minibar_completer(console.buffer)
        line = readline()

    return 'normal'

