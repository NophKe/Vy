from pathlib import Path
import readline
import rlcompleter

class CommandModeCompleter:
    @staticmethod
    def completer(txt, state):
        from __main__ import Editor         # kinda hacky 
        dictionary = Editor.actions.command

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
#            readline.set_completer(self.completer)
            return rv

           
    def __enter__(self):
        self.histfile = Path("~/.vym/command_history").expanduser()
        if not self.histfile.exists():
            self.histfile.touch()

        self._old_complete = readline.get_completer() 

        readline.set_completer(self.completer)
        readline.set_completer_delims(' \t')

        readline.set_history_length(1000)
        readline.clear_history()
        readline.read_history_file(self.histfile)
        readline.parse_and_bind('tab: complete')
        #readline.set_pre_input_hook(stdout_no_cr)
    
    def __exit__(self, *args, **kwargs):
        readline.write_history_file(self.histfile)
        readline.set_completer(self._old_complete)
        #readline.set_pre_input_hook(None)
        
def loop(self):
    self.show_screen()
    ARG = PART = REG = None
    if self._macro_keys and '<CR>' in self._macro_keys:   #NEVER TESTED NOT USED
        user_input, other_lines = self._macro_keys.split('<CR>')
        self._macro_keys = other_lines
    else:
        macro_prefix = self._macro_keys or ''
        self._macro_keys = ''
        try:
#            with stdin_no_echo_nl():
                with CommandModeCompleter():
                    user_input = macro_prefix + input(f':{macro_prefix}').strip()
        except KeyboardInterrupt:
            self.screen.minibar('')
            return 'command'
        except EOFError:
            return 'normal'

    if not user_input:
        return 'normal'

    if user_input.isdigit():
        args = ''
        self.current_buffer.move_cursor(f'#{user_input}')
        self.command_list.append(f':{user_input}<CR>')
        return 'normal'

    if ' ' in user_input:
        cmd, ARG = user_input.split(' ', maxsplit=1)
    else:
        cmd = user_input.strip()

    try:
        action = self.actions.command[cmd]
    except KeyError:
        self.screen.minibar(f'unrecognized command: {cmd}')
        return 'normal'
    self.command_list.append(':{user_input}<CR>')
    self.screen.infobar(f'( Processing Command: {user_input} )')
    return action(arg=ARG, part=PART, reg=REG) or 'normal'
