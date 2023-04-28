from vy.interface.helpers import Completer, one_inside_dict_starts_with
from pathlib import Path

def starts_with_valid_range(string):
    buffer = ''
    for char in string:
        buffer += char
        if buffer.startswith('<') and buffer.endswith('>'):
            return buffer
        if buffer in ('%', '.'):
            return buffer
    return ''

def init(editor):
    global readline
    dictionary = editor.actions.command

    class CommandCompleter(Completer):
        def get_option(self, args):
            if ' ' in args:
                option, value = args.split(' ', maxsplit=1)
                try:
                    option = getattr(editor.current_buffer, 'set_' + option)
                except AttributeError:
                    return [], 0
                return self.get_history()
            elif args.startswith('no'):
                option = args.removeprefix('no')
                return [name[4:] for name in dir(editor.current_buffer) if name.startswith('set_' + option)], len(args) - 2
            else:
                return [name[4:] for name in dir(editor.current_buffer) if name.startswith('set_' + args)], len(args)
                
        def get_buffer(self, args):
            rv = []
            for buff in editor.cache:
                if args in str(buff.path):
                    rv.append(str(buff.path))
            return rv, len(args)

        def get_complete(self):
            user_input = self.buffer.string

            if ' ' in user_input:
                cmd, arg = user_input.split(' ', maxsplit=1)
                cmds = cmd.strip()
                args = arg.strip()
                if cmds in dictionary:
                    func =  dictionary[cmds]
                    if func.with_args and hasattr(func, 'completer'):
                        if func.completer == 'filename':
                            return self.get_filenames(args)
                        elif func.completer == 'buffer':
                            return self.get_buffer(args)
                        elif func.completer == 'option':
                            return self.get_option(args)
                    return self.get_history()
                         
            elif one_inside_dict_starts_with(dictionary, user_input):
                rv = [k for k in dictionary if k.startswith(user_input)]
                return rv, len(user_input)
            return [], 0

    readline = CommandCompleter('command_history', ':', editor)

def loop(self):
    """
    Command mode, main loop.
    """

    ARG = PART = REG = None

    try:
        user_input = readline().lstrip()
    except KeyboardInterrupt:
        self.screen.minibar(' (Command aborted) ')
        return 'normal'

    if not user_input:
        return 'normal'

    elif user_input.isdigit():
        self.current_buffer.cursor_lin_col = int(user_input), 0
        self.save_in_jump_list()
        return 'normal'

    if ' ' in user_input:
        cmd, ARG = user_input.split(' ', maxsplit=1)
    else:
        cmd = user_input.strip()

    cmd = cmd.lstrip(':')
    try:
        action = self.actions.command[cmd]
    except KeyError:
        self.screen.minibar(f'unrecognized command: {cmd}')
        readline.history.pop()
        return 'normal'
    
    cancel = self.screen.minibar(f'( Processing Command: {user_input} )')
    self.registr[':'] = user_input
    
    if ARG:
        rv = action(self, arg=ARG, part=PART, reg=REG)
    else:
        rv = action(self, part=PART, reg=REG)

    cancel()
    return rv or 'normal'
