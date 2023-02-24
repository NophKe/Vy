from vy.interface.helpers import Completer

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

    if user_input.isdigit():
        self.current_buffer.move_cursor(f'#{user_input}')
        return 'normal'

    if ' ' in user_input:
        cmd, ARG = user_input.split(' ', maxsplit=1)
    else:
        cmd = user_input.strip()

    try:
        action = self.actions.command[cmd.lstrip(':')]
    except KeyError:
        self.screen.minibar(f'unrecognized command: {cmd}')
        return 'normal'
    
    info_txt = f'( Processing Command: {user_input} )'
    self.screen.minibar(info_txt)

    if ARG:
        rv = action(self, arg=ARG, part=PART, reg=REG)
    else:
        rv = action(self, part=PART, reg=REG)

    if info_txt in self.screen._minibar_txt:
        self.screen.minibar('')

    return rv or 'normal'
