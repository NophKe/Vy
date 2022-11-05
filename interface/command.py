from pathlib import Path
from vy import keys as k
from vy.filetypes.basefile import DummyLine
from vy.global_config import USER_DIR
from vy.interface.helpers import one_inside_dict_starts_with, Completer

def init(editor):
    global readline
    readline = Completer('command_history', ':', editor, editor.actions.command)

def loop(self):
    """
    Command mode, main loop.
    """

    ARG = PART = REG = None
    try:
        user_input = readline()
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
        action = self.actions.command[cmd]
    except KeyError:
        self.screen.minibar(f'unrecognized command: {cmd}')
        return 'normal'

    self.screen.minibar(f'( Processing Command: {user_input} )')
    if ARG:
        rv = action(self, arg=ARG, part=PART, reg=REG)
    else:
        rv = action(self, part=PART, reg=REG)

    self.screen.minibar('')

    return rv or 'normal'
