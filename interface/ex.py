from code import InteractiveConsole
from vy.interface.helpers import Completer
from __main__ import __dict__ as global_dict
from vy.filetypes.textfile import TextFile
from pathlib import Path # TODO delete this import
import sys

header = 'from __main__ import *\n'
header = '\n'
def loop(editor):

    class Console(InteractiveConsole):
        def write(self, text):
            text = text.splitlines()
            if text:
                editor.screen.minibar(*text)

    class Readline(Completer):
        def get_complete(self):
            source = TextFile(init_text=header+self.buffer.string,
                              cursor=len(header)+self.buffer.cursor -1,
                              path=Path('fake.py')
                              )
            return source.get_completions()
            
    readline = Readline('ex_history', '>>> ', editor,completion_dict=global_dict )
    console = Console(locals=global_dict)
    origin = sys.displayhook
    try:
        line = readline()
        sys.displayhook = lambda arg: editor.screen.minibar(repr(arg))    

        while console.push(line):
            if console.buffer:
                screen = ['    ' + val.removesuffix('\n') for val in console.buffer]
            else:
                screen = []
            line = readline(buffered=screen)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        sys.displayhook = origin
        return 'normal'

