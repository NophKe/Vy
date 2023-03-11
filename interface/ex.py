from code import InteractiveConsole
from vy.interface.helpers import Completer
from vy.global_config import DONT_USE_JEDI_LIB
from __main__ import __dict__ as global_dict
from vy.filetypes.textfile import TextFile
from pathlib import Path # TODO delete this import
import sys
from pprint import pformat

try:
    if DONT_USE_JEDI_LIB:
        raise ImportError

    from jedi import Interpreter
    class Readline(Completer):
        def get_complete(self):
            text = self.buffer.string
            interpreter = Interpreter(text, [global_dict])
            completions = interpreter.complete(fuzzy=False)
    
            if completions:
                lengh = completions[0].get_completion_prefix_length()
                return [item.name_with_symbols for item in completions if hasattr(item, 'name_with_symbols')], lengh 
            return [], 0
except ImportError:
    Readline = Completer


def init(editor):
    global readline
    global console

    readline = Readline('ex_history', '>>> ', editor)
    
    class Console(InteractiveConsole):
        def write(self, text):
            text = text.splitlines()
            if text:
                editor.screen.minibar(*text)
            
    console = Console(locals=global_dict)

def loop(editor):
    origin = sys.displayhook

    try:
        line = readline()
        sys.displayhook = lambda arg: editor.screen.minibar(*pformat(arg).splitlines())    

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

