from vy import global_config
from rlcompleter import Completer 
import readline
from code import InteractiveConsole

try:
    if global_config.DONT_USE_JEDI_LIB:
        raise ImportError
    from jedi import Interpreter
    import os
    import sys

    def jedi_setup_readline(namespace_module, fuzzy=False):
        class JediRL:
            def complete(self, text, state):
                if state == 0:
                    sys.path.insert(0, os.getcwd())
                    # Calling python doesn't have a path, so add to sys.path.
                    try:
                        interpreter = Interpreter(text, [namespace_module])
                        completions = interpreter.complete(fuzzy=fuzzy)

                        self.matches = [
                            text[:len(text) - c._like_name_length] + c.name_with_symbols
                            for c in completions ]
                    finally:
                        sys.path.pop(0)
                try:
                    return self.matches[state]
                except IndexError:
                    return None
        readline.set_completer(JediRL().complete)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set completion-ignore-case on")
        readline.parse_and_bind("set show-all-if-unmodified")
        readline.parse_and_bind("set show-all-if-ambiguous on")
        readline.parse_and_bind("set completion-prefix-display-length 2")
        readline.set_completer_delims('')
except ImportError:
    jedi_setup_readline = None

class CommandCompleter:
    def __init__(self, file):
        histfile = global_config.USER_DIR / file
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
base_env = {'exit': lambda: exec('raise SystemExit')}

def loop(editor, source=None):
    source = source or base_env.copy()
    editor.stop_async_io()
    try:
        console = InteractiveConsole(locals=source)
        with local_completer:
            if jedi_setup_readline is not None:
                jedi_setup_readline(source)
            else:
                readline.set_completer(Completer(console.locals).complete)
            console.interact('','')
    except SystemExit:
        pass
    finally:
        editor.start_async_io()
    return 'normal'
