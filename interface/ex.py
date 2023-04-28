"""
    ***************************
    ****    The Ex Mode    ****
    ***************************

If you only want to execute a code snippet, or get the result of some
random evaluation, you do not need to leave the window.  Just press 'Q'
in normal mode and enter a python prompt.

sys.displayhook is temporarly remapped to print a formatted repr into
the editor minibar.  If the result is a str object, it will be used
instead of its repr.

Just before prompting user input, the 'cb' and 'cw' variables,
respectively for current buffer and current window are inserted into the
global namespace.
"""
from code import InteractiveConsole
from vy.interface.helpers import Completer
from vy.global_config import DONT_USE_JEDI_LIB
from __main__ import __dict__ as global_dict
from vy.filetypes.textfile import TextFile
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
    global displayer

    readline = Readline('ex_history', '>>> ', editor)
    
    class Console(InteractiveConsole):
        def write(self, text):
            text = text.splitlines()
            if text:
                editor.screen.minibar(*text)
            
    console = Console(locals=global_dict)

    def displayer(arg):
        if isinstance(arg, str):
            editor.screen.minibar(arg)    
        else:
            editor.screen.minibar(*pformat(arg).splitlines())    
        
def loop(editor):
    origin = sys.displayhook
    if 'cb' not in global_dict:
        global_dict['cb'] = editor.current_buffer
    if 'cw' not in global_dict:
        global_dict['cw'] = editor.current_window

    try:
        line = readline()
        sys.displayhook = displayer
        editor.registr['>'] = line

        while console.push(line):
            if console.buffer:
                screen = ['    ' + val.removesuffix('\n') for val in console.buffer]
            else:
                screen = []
            line = readline(buffered=screen)
            editor.registr['>'] += line
            
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        del global_dict['cb']
        del global_dict['cw']
        sys.displayhook = origin
        return 'normal'

