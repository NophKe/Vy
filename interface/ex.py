"""
    ***************************
    ****    The Ex Mode    ****
    ***************************

If you only want to execute a code snippet, or get the result of some
random evaluation, you do not need to leave the window.  Just press 'Q'
in normal mode and enter a python prompt.

sys.displayhook is temporarly remapped to print a formatted repr into
the editor minibar.  If the result is a str object, its value will be 
used instead of its repr.

Execution takes place in a separated namespace that gets created just 
before prompting user input for the first time. It will be populated
with 3 shortcut variables that will be updated at every new prompt.

The clear() function may be used to restore the name-space to its
original state containing only the builtins and the following variables.

    - 'ed' is the editor instance
    - 'cb' is editor.current_buffer
    - 'cw' is editor.current_window
    - clear() to reset the namespace
"""
from code import InteractiveConsole
from vy.interface.helpers import Completer
from vy.global_config import DONT_USE_JEDI_LIB
import sys
from pprint import pformat
import vy
from vy.editor import _Editor

global_dict = {}

try:
    if DONT_USE_JEDI_LIB:
        raise ImportError
    from jedi import Interpreter
    
    class Readline(Completer):
        def get_complete(self):
            global global_dict
            text = self.buffer.string
            interpreter = Interpreter(text, [global_dict])
            completions = interpreter.complete(fuzzy=False)
    
            if completions:
                lengh = completions[0].get_completion_prefix_length()
                return [item.name_with_symbols for item in completions if hasattr(item, 'name_with_symbols')], lengh 
            return [], 0
            
except ImportError:
    Readline = Completer

def init(editor: _Editor):
    global global_dict

    global readline
    readline = Readline('ex_history', '>>> ', editor)
    
    class Console(InteractiveConsole):
        def write(self, text):
            text = text.splitlines()
            if text:
                editor.screen.minibar(*text)
    global console
    console = Console(locals=global_dict)
        

def my_print(*args, **kwargs):
    to_print = []
    for arg in args:
        if isinstance(arg, str):
            to_print.extend(arg.splitlines())
        else:
            to_print.extend(repr(arg).splitlines())
    return '\n'.join(to_print)
        
def populate_namespace(editor):
    def my_help(*args, **kwargs):
        editor.stop_async_io()
        help(*args, **kwargs)
        editor.start_async_io()
    global_dict['cb'] = editor.current_buffer
    global_dict['cw'] = editor.current_window
    global_dict['ed'] = editor
    global_dict['vy'] = vy
    global_dict['print'] = my_print    
    global_dict['help'] = my_help
    global_dict['clear'] = global_dict.clear

def loop(editor: _Editor):
    def my_display_hook(arg):
        if isinstance(arg, str):
            return editor.screen.minibar(*arg.splitlines())
        else:
            return editor.screen.minibar(*pformat(arg).splitlines())
#        editor.screen.minibar(repr(arg))
    
    populate_namespace(editor)
    sys.displayhook = my_display_hook
    try:
        editor.registr['>'] = line = readline()
        more = console.push(line)
        
        if more and line:        
            screen = ['>>> ' + line.removesuffix('\n')]
            while more:
                line = readline(buffered=screen)
                screen.append('... ' + line.removesuffix('\n'))
                editor.registr['>'] += line
                more = console.push(line)
    finally:
        sys.displayhook = sys.__displayhook__ # back to original
#        return 'ex'
        return 'normal'

