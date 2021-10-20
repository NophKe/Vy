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
        readline.clear_history()
        readline.read_history_file(self.histfile)
        readline.parse_and_bind('tab: complete')
    
    def __exit__(self, *args, **kwargs):
        readline.write_history_file(self.histfile)
        readline.set_completer(self._old_complete)
        
def loop(self):
    self.screen.minibar('')
    self.screen.infobar('')
    self.screen.bottom()

    with CommandModeCompleter():
        if self._macro_keys and '<CR>' in self._macro_keys:
            user_input, other_lines = self._macro_keys.split('<CR>')
            self._macro_keys = other_lines
        else:
            macro_prefix = self._macro_keys or ''
            self._macro_keys = ''
            try:
                user_input = macro_prefix + input(f':{macro_prefix}').strip()
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
            args = ''

        return self.actions.command.get(key, lambda x: 'normal')(args) or 'normal'
