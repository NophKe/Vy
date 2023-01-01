from pathlib import Path
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
        self.prompt = f'\x1b[39;49;1m{prompt}\x1b[39;49;22m'
        self.editor = editor
        self.reader = editor.read_stdin
        self.screen = editor.screen
        self.buffer = DummyLine()
        self.dictionary = completion_dict

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
                elif key == k.CR and self.state:
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
            screen.minibar_completer()
            screen.minibar()

    def select_item(self):
        to_insert, to_delete = self.screen.minibar_completer.select_item()
        text = self.buffer.string
        cursor = self.buffer.cursor
        self.state = ''
        rv = ''
        rv += text[:cursor - to_delete]
        rv += to_insert
        rv += text[cursor:]
        self.buffer.string = rv
        self.buffer.cursor += len(to_insert) - to_delete
        return rv

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
            completion, prefix = getattr(self, 'get_' + self.state)()
            self.screen.minibar_completer(completion, prefix)

    def get_history(self):
        return [item for item in self.history if item.startswith(self.buffer.string)], len(self.buffer.string)

    def get_complete(self):
        user_input = self.buffer.string

        if ' ' in user_input:
            cmd, arg = user_input.split(' ', maxsplit=1)
            cmd = cmd.strip()
            args = arg.strip()
            if cmd in self.dictionary and self.dictionary[cmd].with_args:   
                rv = [str(k).removeprefix(args) for k in Path('.').iterdir() if str(k).startswith(args)]
                prefix = len(arg)
                return rv, prefix

        elif one_inside_dict_starts_with(self.dictionary, user_input):
            rv = [k for k in self.dictionary if k.startswith(user_input)]
            return rv, len(user_input)
        return [], 0

    def complete(self):
        if not self.state:
            self.state = 'complete'
            self.update_minibar_completer()
        else: 
            self.screen.minibar_completer.move_cursor_up()

    def move_left(self):
        if self.buffer.cursor > 0:
            self.buffer.cursor -= 1

    def move_right(self):
        if self.buffer.cursor < len(self.buffer.string):
            self.buffer.cursor += 1

    def move_cursor_up(self):
        if not self.state:
            self.state = 'history'
            self.update_minibar_completer()
        else: 
            self.screen.minibar_completer.move_cursor_up()

    def move_cursor_down(self):
        if not self.state:
            return
        else:
            self.screen.minibar_completer.move_cursor_down()

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
