from vy.interface.helpers import Completer

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
    readline = Completer('command_history', ':', editor, editor.actions.command)

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
        return 'normal'
    
    info_txt = f'( Processing Command: {user_input} )'
    self.screen.minibar(info_txt)
    self.registr[':'] = user_input
    
    if ARG:
        rv = action(self, arg=ARG, part=PART, reg=REG)
    else:
        rv = action(self, part=PART, reg=REG)

    if info_txt in self.screen._minibar_txt:
        self.screen.minibar('')

    return rv or 'normal'
