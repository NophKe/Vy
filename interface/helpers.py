from pathlib import Path
#import readline
from ..global_config import USER_DIR
from ..filetypes.basefile import DummyLine
from .. import keys as k

class Completer:
    def __init__(self, file, prompt, editor, completion_dict={}):
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
        self.prompt = f'\x1b[39;49;1m{prompt}\x1b[39;49;22m'
        self.editor = editor
        self.reader = editor.read_stdin
        self.screen = editor.screen
        self.buffer = DummyLine()
        self.dictionary = completion_dict
        self.view_start = 0

    def __call__(self):
        """
        Read from stdin until ^C, ^D or newline.
        """
        self.buffer.string = ''
        self.buffer.cursor = 0
        buffer = self.buffer
        screen = self.screen
        reader = self.reader

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
                elif key == k.CR and self.state and self.completion:
                    self.buffer.string = self.select_item()
                elif key == k.CR:
                    self.history.append(buffer.string)
                    return buffer.string
                elif key.isprintable():
                    buffer.insert(key)
                else:
                    return

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
            completion = getattr(self, 'get_' + self.state)()
            if completion != self.completion:
                self.max_selected = len(completion) - 1
                self.selected = 0
                self.view_start = 0
                self.completion = completion
            #to_print = [f'| {self.buffer.string}{k} ' if index != self.selected
                   #else f"|\x1b[7m {self.buffer.string}{k} \x1b[27m" 
                   #for index, k in enumerate(completion)]
            to_print = [f'| {k} ' if index != self.selected
                   else f"|\x1b[7m {k} \x1b[27m" 
                   for index, k in enumerate(completion)][self.view_start:self.view_start+8]
            self.screen.minibar_completer(*to_print)

    def get_history(self):
        return [item for item in self.history if item.startswith(self.buffer.string)] #[-7:]


    def get_complete(self):
        user_input = self.buffer.string

        if ' ' in user_input:
            cmd, args = user_input.split(' ', maxsplit=1)
            cmd = cmd.strip()
            args = args.strip()
        else:
            cmd = ''

        rv = list()
            
        if cmd and self.dictionary[cmd].with_args:
            if not args: #default to completing filenames
                rv.extend([str(k).removeprefix(args) for k in Path('.').iterdir() if str(k).startswith(args)])
            else:
                rv.extend([str(k).removeprefix(args) for k in Path('.').iterdir() if str(k).startswith(args)])

# BUGGY 

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
        self.view_start = 0
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
        elif self.selected > 0:
            self.selected -= 1
        else:
            self.selected = self.max_selected

        if self.selected <= self.view_start:
            self.view_start = self.selected
        if self.selected > self.view_start + 7:
            self.view_start = self.selected - 7

    def move_cursor_down(self):
        if not self.state:
            return
        if self.selected == self.max_selected:
            self.selected = 0
        else:
            self.selected += 1

        if self.selected <= self.view_start:
            self.view_start = self.selected
        if self.selected > self.view_start + 7:
            self.view_start = self.selected - 7

    def select_item(self):
        item = self.completion[self.selected]
        rv = self.buffer.string + item.removeprefix(self.buffer.string)
        self.buffer.string = rv
        self.state = ''
        self.buffer.cursor = len(self.buffer.string)
        return rv

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
