from ..global_config import USER_DIR
from rlcompleter  import Completer 
import readline
from pathlib import Path
from code import InteractiveConsole

class CommandCompleter:
    def __init__(self, file):
        histfile = USER_DIR / file
        if not histfile.exists():
            histfile.touch()
        restric = set(histfile.read_text().splitlines(True))
        histfile.write_text(''.join(restric))
        self.histfile = histfile

    def __enter__(self):
        self._old_history = [ readline.get_history_item(idx) 
                                for idx in range(readline.get_current_history_length())]
        self._old_complete = readline.get_completer() 
        readline.set_completer_delims(' \t')
        readline.set_history_length(1000)
        readline.clear_history()
        readline.read_history_file(self.histfile)
        readline.parse_and_bind('tab: complete')
  
    def __exit__(self, *args, **kwargs):
        readline.write_history_file(self.histfile)
        readline.set_completer(self._old_complete)
        readline.clear_history()
        for item in self._old_history:
            readline.add_history(item)

local_completer = CommandCompleter('python_history')

def loop(editor, source=None):
    try:
        editor.stop_async_io()
        console = InteractiveConsole(locals={'Editor': editor})#, editor=editor)
        if source:
            print('=====')
            for line in source.splitlines(True):
                if line != '\n':
                    console.push(line)
            print('=====')
        
        try:
            with local_completer:
                readline.set_completer(Completer(console.locals).complete)
                console.interact()
        except SystemExit:
            pass
        return 'normal'

    finally:
        editor.start_async_io()
