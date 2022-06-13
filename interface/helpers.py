from pathlib import Path
import readline
from ..global_config import USER_DIR

class CommandCompleter:
    def completer(self, txt, state):
        '''This method must be overriden in concrete implementations.'''
        return ''

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
        #readline.set_pre_input_hook(stdout_no_cr)
    def __exit__(self, *args, **kwargs):
        readline.write_history_file(self.histfile)
        readline.set_completer(self._old_complete)
        readline.clear_history()
        for item in self._old_history:
            readline.add_history(item)
        #readline.set_pre_input_hook(None)


def do(*arg_list, mode=None):
    doc = 'This command is does the following actions:\n'
    for arg_item in arg_list:
        if callable(arg_item) and arg_item.__doc__:
            doc += arg_item.__doc__ + '\n'
        elif isinstance(arg_item, str):
            doc += f"lambda function where x is the editor and arg the following of the line:\n lambda x, arg: {arg_item}" 
    def func(ed, cmd):
        for arg_item in arg_list:
            if callable(arg_item):
                arg_item(ed, cmd)
            elif isinstance(arg_item, str):
                eval(f"lambda x,arg: {arg_item}")(ed, cmd) 
        return mode
    func.__doc__ = doc
    return func

def resolver(mapping, key=None, default=None):
    tried = set()
    while True:
        try:
            rv = mapping[key]
        except KeyError:
            return default
        if rv in tried:
            raise RecursionError
        if callable(rv):
            return rv
        else:
            tried.add(rv)
            key = rv

def one_inside_dict_starts_with(dictio, pattern):
    maybe = False
    for key in dictio:
        try:
            if key.startswith(pattern):
                if key != pattern:
                    return True
                else:
                    maybe = True
        except AttributeError:
            pass
    return maybe
