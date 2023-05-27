from pathlib import Path
from vy.keys import _escape
from vy.global_config import USER_DIR
from vy.utils import DummyLine
from vy import keys as k

class Completer:
    def __init__(self, file, prompt, editor):
        histfile = USER_DIR / file
        if not histfile.exists():
            histfile.touch()
        self.histfile = histfile
        self.history = [ item for item in histfile.read_text().splitlines() ]
        self.state = ''
        self.prompt = f'\x1b[39;1m{prompt}\x1b[39;22m'
        self.editor = editor
        self.reader = editor.read_stdin
        self.screen = editor.screen
        self.buffer = DummyLine()
        self._last_comp = self.state, self.buffer.string, self.buffer.cursor
        self.buffered = []
    
    def __call__(self, buffered=None):
        """
        Read from stdin until ^C, ^D or newline.
        """
        self.state = ''
        self.buffer.string = ''
        self.buffer.cursor = 0
        buffer = self.buffer
        screen = self.screen
        reader = self.reader
        
        if buffered:
            self.buffered = buffered

        try:
            while True:
                self.update_minibar()
                key = reader()
                if key in (k.backspace, k.linux_backpace):
                    buffer.backspace()
                    self.state = ''
                elif key == k.C_V:
                    buffer.insert(reader())
                elif key == k.suppr:
                    buffer.suppr()
                    self.state = ''
                elif key == k.left:
                    self.move_left()
                elif key == k.right:
                    self.move_right()
                elif key == '\t':
                    self.start_complete()
                elif key == k.up:
                    self.move_cursor_up()
                elif key == k.down:
                    self.move_cursor_down()
                elif key == k.C_C or key == '\x1b':
                    if self.state:
                        self.state = ''
                        continue
                    raise KeyboardInterrupt
                elif key == k.CR:
                    if self.state:
                        self.select_item()
                    else:
                        self.history.append(buffer.string)
                        self.histfile.write_text('\n'.join(self.history))
                        return buffer.string

                elif key.isprintable():
                    buffer.insert(key)
                else:
                    self.editor.warning(f'unrecognized key: {_escape(key)}')
                    self.state = ''
        finally:
            self.buffered = []
            screen.minibar_completer.give_up()
            screen.minibar('')

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

    def update_minibar(self):
        mini_text = self.prompt + ''.join(
                char if idx != self.buffer.cursor
                else f'\x1b[7m{char}\x1b[27m' 
                for idx, char in enumerate(self.buffer.string + ' ')
                )
        self.screen.minibar(*(self.buffered + [mini_text]))

    def get_filenames(self, arg=None):
        if arg is None:
            arg = self.buffer.string
        user_input = Path(arg)

        if arg.endswith('/') and (pth := Path(arg)).is_dir():
            pth = user_input.iterdir() 
        else:
            pth = user_input.parent.iterdir()

        path_list = [k for k in pth if str(k).startswith(arg)]
        dir_list = [k for k in path_list if k.is_dir()]
        file_list = [k for k in path_list if k not in dir_list]
        rv = [str(k) + '/' for k in dir_list]
        rv.extend(str(k) for k in file_list)
        #if len(rv) == 1 and user_input.is_dir():
            #prefix = len(arg)
        return rv, len(arg)

    def _get_completions(self):
        if self.state:
            if self.buffer.cursor != len(self.buffer.string):
                self.state = ''
            else:
                completer = getattr(self, 'get_' + self.state)
                rv = completer()
                self._last_comp = self.state, self.buffer.string, self.buffer.cursor
                return rv
        return [], 0

    def check_completion(self):
        if self._last_comp == (self.state, self.buffer.string, self.buffer.cursor):
            return False
        return True
    
    def update_minibar_completer(self):
        if not self.state:
            self.screen.minibar_completer.give_up()
        else:
            self.screen.minibar_completer.set_callbacks(lambda: self._get_completions(), lambda: self.check_completion())

    def get_history(self):
        return [item for item in self.history if item.startswith(self.buffer.string)], len(self.buffer.string)
    
    def get_complete(self):
        return [], 0

    def start_complete(self):
        if not self.state:
            self.state = 'complete'
            self.update_minibar_completer()
        elif not self.editor.screen.minibar_completer.completion:
            pass
        elif len(self.editor.screen.minibar_completer.completion) == 1:
            self.select_item()
        else:
            self.screen.minibar_completer.move_cursor_down()

    def move_left(self):
        if self.buffer.cursor > 0:
            self.buffer.cursor -= 1
        self.state = ''

    def move_right(self):
        if self.buffer.cursor < len(self.buffer.string):
            self.buffer.cursor += 1
        self.state = ''

    def move_cursor_up(self):
        if self.state:
            self.screen.minibar_completer.move_cursor_up()
        else: 
            self.state = 'history'
            self.update_minibar_completer()
            self.screen.minibar_completer.move_cursor_up()

    def move_cursor_down(self):
        if self.state:
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
