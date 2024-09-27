from pathlib import Path
import atexit

from vy import keys as k
from vy.keys import _escape
from vy.global_config import USER_DIR
from vy.utils import DummyLine

class Completer:
    def __init__(self, file, prompt, editor):
        histfile = USER_DIR / file
        if not histfile.exists():
            histfile.touch()
        self.histfile = histfile
        self.history = list({item:None for item in histfile.read_text().splitlines()}.keys())
        self.state = ''
        self.prompt = f'\x1b[97;1m{prompt}\x1b[97;22m'
        self.editor = editor
        self.screen = editor.screen
        self.buffer = DummyLine()
#        self._last_comp = self.state, self.buffer.string, self.buffer.cursor
        self.buffered = []
        self.selected = -1
        atexit.register(lambda: self.histfile.write_text('\n'.join(self.history)))
    
    def __call__(self, buffered=None):
        """
        Read from stdin until ^C, ^D or newline.
        """
        self.state = ''
        self.buffer.string = ''
        self.buffer.cursor = 0
        buffer = self.buffer
        screen = self.screen
        
        if buffered:
            self.buffered = buffered

        try:
            while True:
                self.update_minibar()
                key = self.editor.read_stdin()
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
                        if (content := buffer.string.strip()):
                            if content not in self.history:
                                self.history.append(content)
                            else:
                                self.history.pop(self.history.index(content))
                                self.history.append(content)
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
        # wait for result
        try:
            to_insert, to_delete = self.completion[self.selected], self.prefix_len
        except IndexError:
            self.selected = -1
            self.state = ''
            return
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
        if not self.state:
            self.screen.minibar_completer.give_up()
        elif self.buffer.cursor != len(self.buffer.string):
            self.state = ''
        else:
            self.completion, self.prefix_len = getattr(self, 'get_' + self.state)()
            if self.selected > len(self.completion) - 1:
                self.selected = 0
            if self.selected < 0:
                self.selected = 0
            self.screen.minibar_completer(lambda: (self.completion, self.selected))

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
        rv = sorted([str(k) + '/' for k in dir_list])
        rv.extend(sorted(str(k) for k in file_list))
        #if len(rv) == 1 and user_input.is_dir():
            #prefix = len(arg)
        return rv, len(arg)

    def get_history(self):
        result = [item for item in reversed(self.history) if item.startswith(self.buffer.string)]
        return result, len(self.buffer.string)
    
    def get_complete(self):
        return [], 0

    def start_complete(self):
        if not self.state:
            self.state = 'complete'
#        elif not self.completion:
#            self.selected = 0
        elif len(self.completion) == 1:
            self.select_item()
        else:
            self.move_cursor_down()
            
    def move_cursor_up(self):
        if self.state:
            if self.selected > 0:
                self.selected -= 1
            else:
                self.selected = len(self.completion) - 1
        else: 
            self.selected = 0
            self.state = 'history'
        
    def move_cursor_down(self):
        if self.state:
            if self.selected == len(self.completion):
                self.selected = 0
            else:
                self.selected += 1
        else:
            self.selected = len(self.completion)
            self.state = 'history'
            
    def move_left(self):
        if self.buffer.cursor > 0:
            self.buffer.cursor -= 1
        self.state = ''

    def move_right(self):
        if self.buffer.cursor < len(self.buffer.string):
            self.buffer.cursor += 1
        self.state = ''

def one_inside_dict_starts_with(dic, pattern):
    return (pattern in dic) or (any(key.startswith(pattern) for key in dic))
