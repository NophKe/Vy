from pathlib import Path
from vy import keys as k
#from vy.interface.helpers import CommandCompleter
from vy.filetypes.basefile import InputBuffer
from vy.global_config import USER_DIR
from vy.interface.helpers import one_inside_dict_starts_with

class Completer:
    def __init__(self, file):
        histfile = USER_DIR / file
        if not histfile.exists():
            histfile.touch()
        restric = set(histfile.read_text().splitlines(True))
        histfile.write_text(''.join(restric))
        self.histfile = histfile
        self.history = [ item.removesuffix('\n') for item in restric ]
        self.state = ''
        self.max_selected = 0
        self.selected = 0
        self.completion = list()
        self.prompt = '\x1b[39;49;1m:\x1b[39;49;22m'
        self.editor = None
        self.buffer = InputBuffer()

    def __call__(self, editor):
        """
        Read from stdin until ^C, ^D or newline.
        """
        if self.editor is None:
            self.editor = editor
            self.dictionary = editor.actions.command
            self.screen = editor.screen

        self.buffer.string = ''
        self.buffer.cursor = 0
        buffer = self.buffer
        screen = self.screen
        reader = editor.read_stdin

        self.update_minibar()
        try:
            while True:
                key = reader()
                if key == k.backspace:
                    buffer.backspace()
                elif key == k.suppr:
                    buffer.suppr()
                elif key == k.left:
                    self.move_left()
                elif key == k.right:
                    self.move_right()
                elif key == '\t':
                    self.complete()
                elif key == k.up:
                    self.move_cursor_up()
                elif key == k.down:
                    self.move_cursor_down()
                elif key == k.C_C or key == '\x1b':
                    raise KeyboardInterrupt
                elif key == k.CR and self.state:
                    rv = self.select_item()
                    self.history.append(rv)
                    return rv 
                elif key == k.CR:
                    self.history.append(buffer.string)
                    return buffer.string
                else:
                    buffer.insert(key)

                self.update_minibar_completer()
                self.update_minibar()

        finally:
            self.give_up()
            screen.minibar_completer()
            screen.minibar()
        assert False
        return buffer.string

    def update_minibar(self):
        mini_text = self.prompt + ''.join(
                char if idx != self.buffer.cursor
                else f'\x1b[7m{char}\x1b[27m' 
                for idx, char in enumerate(self.buffer.string + ' ')
                )
        self.screen.minibar(mini_text)
    
    def update_minibar_completer(self):
        if not self.state:
            self.screen.minibar_completer()
        else:
            completer = getattr(self, 'get_' + self.state)
            completion = completer()
            if completion != self.completion:
                self.max_selected = len(completion) - 1
                self.selected = 0
                self.completion = completion
            to_print = ''.join([f'| {k}' if index != self.selected
                   else f"|\x1b[7m {k} \x1b[27m" 
                   for index, k in enumerate(completion)])
            self.screen.minibar_completer(to_print)

    def get_history(self):
        self.completion = [item for item in self.history if item.startswith(self.buffer.string)][-5:]
        return self.completion


    def get_complete(self):
        user_input = self.buffer.string
        rv = list()
        if user_input in self.dictionary:
            self.buffer.insert(' ')
            
        if user_input.strip() in self.dictionary:
            if self.dictionary[user_input.strip()].with_args:
                rv.extend([str(k) for k in Path('.').iterdir()])
            else:
                pass
        elif one_inside_dict_starts_with(self.dictionary, user_input):
            rv.extend([k for k in self.dictionary if k.startswith(user_input)])

        return rv

    def complete(self):
        if not self.state:
            self.state = 'complete'
        else: 
            self.move_cursor_up()

    def give_up(self):
        self.state = ''
        self.selected = 0
        self.completion = list()

    def move_left(self):
        if self.buffer.cursor > 0:
            self.buffer.cursor -= 1

    def move_right(self):
        if self.buffer.cursor < len(self.buffer.string):
            self.buffer.cursor += 1

    def move_cursor_up(self):
        if not self.state:
            self.state = 'history'
        elif self.selected < self.max_selected:
            self.selected += 1
        else:
            self.selected = 0

    def move_cursor_down(self):
        if self.selected > self.max_selected:
            self.selected = 0
        else:
            self.selected += 1

    def select_item(self):
        return self.buffer.string + self.completion[self.selected] 

readline = Completer('command_history')


def loop(self):
    """
    Command mode, main loop.
    """

    ARG = PART = REG = None
    try:
        user_input = readline(self)
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

    self.screen.infobar(f'( Processing Command: {user_input} )')
    if ARG:
        rv = action(self, arg=ARG, part=PART, reg=REG)
    else:
        rv = action(self, part=PART, reg=REG)

    return rv or 'normal'
