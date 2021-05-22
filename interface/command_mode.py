from pathlib import Path
import readline

from ..actions import *
from .helpers import resolver, do

class CommandModeCompleter:
    @staticmethod
    def completer(txt, state):
        readline.redisplay()
        line = readline.get_line_buffer()
        if not line:
            rv = [k for k in dictionary][state] + ' '
            return rv
        
        if line and (' ' not in line):
            rv = [k for k in dictionary.keys() 
                    if isinstance(k, str) and k.startswith(txt)
                    ][state] + ' '
            return rv
        
        if line in dictionary:
            readline.insert_text(' ')

        if line.startswith( ('r ', 'e ', 'edit ', 'vsplit ', 
                        'w ', 'w! ', 'write ', 'write! ')):
            readline.set_completer(None)
            rv = readline.get_completer(txt, state)
            readline.set_completer(self.completer)
            return rv

           
    def __enter__(self):
        self.histfile = Path("~/.vym/command_history").expanduser()
        if not self.histfile.exists():
            self.histfile.touch()

        self._old_complete = readline.get_completer() 

        readline.set_completer(self.completer)
        readline.set_completer_delims(' \t')

        readline.set_history_length(1000)
        readline.read_history_file(self.histfile)
        readline.parse_and_bind('tab: complete')
    
    def __exit__(self, *args, **kwargs):
        readline.write_history_file(self.histfile)
        readline.set_completer(self._old_complete)
        
def loop(self):
    self.screen.minibar('')
    self.screen.bottom()

    with CommandModeCompleter():
        try:
            user_input = input(':').strip()
        except KeyboardInterrupt:
            return 'command'
        except EOFError:
            return 'normal'

        if user_input.isdigit():
            self.current_buffer.move_cursor(f'#{user_input}')

        if ' ' in user_input:
            cmd, args = user_input.split(' ', maxsplit=1)
            key = cmd
        else:
            key = user_input
            args = None
        
        return (resolver(dictionary,key, default=do(mode='normal'))(self, args) 
                or 'normal')

def DO_nmap(ed, arg):
    if not arg or not ' ' in arg:
        ed.warning('[syntax] :nmap key mapping')
    key, value = arg.split(' ', maxsplit=1)
    ed.current_buffer.stand_alone_commands[key] = lambda ed,cmd: ed.push_macro(value)

dictionary = {
    'nmap'  : DO_nmap,
# Meta commands
    '!'     : DO_system,
    'set'   : DO_set,
    'help'  : DO_help,
    'cd'    : DO_chdir,

# change mode
    'visual': 'vi',
    'vi'    : DO_nothing,
    'python': do(mode='python'),

# See what's in the cache
    'file'  : 'buffers',
    'ls'    : 'buffers',
    'buffers'   : lambda ed, cmd: ed.warning(str(ed.cache)),

# see what's in registers
    'registers' : lambda ed, cmd: ed.warning(str(ed.register)),
    'reg'   : 'registers',
# misc
    'read'  : 'r',
    'r'     : read_file,
    'on'    : 'only',
    'only'  : DO_keep_only_current_window,
    'vsplit': DO_vsplit,
    'eval'  : DO_eval_buffer,

# edit
    'edit'  : 'e',
    'e'     : do(DO_edit, mode='normal'),

# Quitting
    'quit'  : 'q',
    'q'     : DO_leave_current_window,

    'quitall'   : 'qa',
    'quita' : 'qa',
    'qall'  : 'qa',
    'qa'    :  DO_exit_nice,

    'quitall!'  : 'qa!',
    'quita!'    : 'qa!',
    'qall!' : 'qa!',
    'qa!'   : DO_exit_hard,

    'quit!' : 'q!',
    'q!'    : DO_force_leave_current_window ,

    'wq'    : do(DO_try_to_save, DO_exit_nice),
    'wqa'   : do(DO_save_all, DO_exit_nice ),
    'wqa!'  : do(DO_force_to_save, DO_save_all, DO_exit_hard ),

# Saving
    'wall'  : 'wa',
    'wa'    : DO_save_all,

    'write' : 'w',
    'w'     : DO_try_to_save, 

    'write!'    : 'w!',
    'w!'    : DO_force_to_save,
}
