"""This module is a mess that handles screen rendering"""
from os import get_terminal_size
from sys import stdout

from vy.global_config import DONT_USE_PYGMENTS_LIB 

MAGIC_VALUE = 100

try:
    if DONT_USE_PYGMENTS_LIB:
        raise ImportError

    from pygments.token import (Keyword, Name, Comment, 
                                String, Error, Number, Operator, 
                                Generic, Token, Whitespace, Text)
    colorscheme = {
        Token:              '',
        Whitespace:         'gray',         Comment:            '/gray/',
        Comment.Preproc:    'cyan',         Keyword:            '*blue*',
        Keyword.Type:       'cyan',         Operator.Word:      'magenta',
        Name.Builtin:       'cyan',         Name.Function:      'green',
        Name.Namespace:     '_cyan_',       Name.Class:         '_green_',
        Name.Exception:     'cyan',         Name.Decorator:     'brightblack',
        Name.Variable:      'red',          Name.Constant:      'red',
        Name.Attribute:     'cyan',         Name.Tag:           'brightblue',
        String:             'yellow',       Number:             'blue',
        Generic.Deleted:    'brightred',    Text:               '',
        Generic.Inserted:   'green',        Generic.Heading:    '**',
        Generic.Subheading: '*magenta*',    Generic.Prompt:     '**',
        Generic.Error:      'brightred',    Error:              '_brightred_',
    }
except ImportError:
    colorscheme = {'': ''}

codes = {
        ""          : "",
# Text Formatting Attributes
        "reset"     : "\x1b[39;49;00m", "bold"      : "\x1b[01m",
        "faint"     : "\x1b[02m",       "standout"  : "\x1b[03m",
        "underline" : "\x1b[04m",       "blink"     : "\x1b[05m",
        "overline"  : "\x1b[06m",
# Dark Colors
        "black"     :  "\x1b[30m",      "red"       :  "\x1b[31m",
        "green"     :  "\x1b[32m",      "yellow"    :  "\x1b[33m",
        "blue"      :  "\x1b[34m",      "magenta"   :  "\x1b[35m",
        "cyan"      :  "\x1b[36m",      "gray"      :  "\x1b[37m",
# Light Colors
        "brightblack"   :  "\x1b[90m",  "brightred"     :  "\x1b[91m",
        "brightgreen"   :  "\x1b[92m",  "brightyellow"  :  "\x1b[93m",
        "brightblue"    :  "\x1b[94m",  "brightmagenta" :  "\x1b[95m",
        "brightcyan"    :  "\x1b[96m",  "white"         :  "\x1b[97m",
    }

def get_prefix(token):
    if token in colorscheme:
        return colorscheme[token]
    accu = ''
    for ttype in token.split('.'):
        if ttype in colorscheme:
            colorscheme[token] = colorscheme[ttype]
        accu = f'{accu}{"." if accu else ""}{ttype}'
        if accu in colorscheme:
            colorscheme[token] = colorscheme[accu]
    if token in colorscheme:
        return colorscheme[token]

def _resolve_prefix(color_string):
    result: str = ''
    if color_string[:1] == color_string[-1:] == '/':
        result += "\x1b[02m"
        color_string = color_string[1:-1]
    if color_string[:1] == color_string[-1:] == '*':
        result += "\x1b[01m"
        color_string = color_string[1:-1]
    if color_string[:1] == color_string[-1:] == '_':
        result += "\x1b[04m"
        color_string = color_string[1:-1]
    result += codes[color_string]
    return result

colorscheme = {repr(key): _resolve_prefix(value) for key, value in colorscheme.items()}


def get_rows_needed(number):
    if number < 800: return 3
    elif number < 9800: return 4
    elif number < 99800: return 5
    elif number < 999800: return 6
    return len(str(number))

def expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
    number = f'{on_lin:{get_rows_needed(on_lin)}}: '
    line =  f'\x1b[00;90;40m{number}\x1b[39;49m'

    retval: list = list()
    on_col: int = len(number)
    cursor_col += on_col - 1
    esc_flag: bool = False
    cursor_flag: bool = False

    char: str
    for char in text:
        if esc_flag:
            line += char
            if char == 'm':
                esc_flag = False
            continue

        if char == '\x1b':
            esc_flag = True
            line += char
            continue

        if on_col ==  max_col:
            line += '\x1b[39;49m'
            retval.append(line)
            line = '\x1b[90;40m' + ' ' * len(number)+ '\x1b[39;49m'
            cursor_col  = cursor_col - (max_col - len(number))
            on_col = len(number)
            esc_flag = False

        cursor_flag = bool((on_col, on_lin) == (cursor_col, cursor_lin))
        if cursor_flag:
            line += '\x1b[5;7m'

        if char == '\t':
            nb_of_tabs =  tab_size - (on_col % tab_size)
            line += ' ' * nb_of_tabs
            on_col += nb_of_tabs
            cursor_col += (nb_of_tabs-1)
        else:
            on_col += 1
            line += char
        if cursor_flag:
            line += '\x1b[25;27m'

    retval.append(line + (' ' * (max_col - on_col)))
    return retval

def expandtabs(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
    retval: list = list()
    line: str = '\x1b[39;49m'
    on_col: int = 1
    cursor_col += on_col - 1
    esc_flag: bool = False
    cursor_flag: bool = False

    char: str
    for char in text:
        if esc_flag:
            line += char
            if char == 'm':
                esc_flag = False
            continue

        if char == '\x1b':
            esc_flag = True
            line += char
            continue

        if on_col ==  max_col:
            line += '\x1b[39;49m'
            retval.append(line)
            line = '\x1b[39;49m'
            cursor_col  = cursor_col - max_col + 1
            on_col = 1
            esc_flag = False

        cursor_flag = bool((on_col, on_lin) == (cursor_col, cursor_lin))
        if cursor_flag:
            line += '\x1b[5;7m'

        if char == '\t':
            nb_of_tabs =  tab_size - (on_col % tab_size)
            line += ' ' * nb_of_tabs
            on_col += nb_of_tabs
            cursor_col += (nb_of_tabs-1)
        else:
            on_col += 1
            line += char
        if cursor_flag:
            line += '\x1b[25;27m'

    retval.append(line + (' ' * (max_col - on_col)))
    return retval

class Window():
    def __init__(self, parent, shift_to_col, shift_to_lin, buff):
        self.parent: Window = parent
        self.shift_to_col: int = shift_to_col
        self.shift_to_lin: int = shift_to_lin
        self.buff = buff
        self._v_split_flag: bool = False
        self.v_split_shift: int = 0
        self._focused: Window = self 

    def set_focus(self):
        if self.parent is self:
            return
        elif self.parent._focused is not self:
            self.parent._focused = self
        self.parent.set_focus()

    def get_left_buffer(self, caller=None):
        if caller is self:
            return self
        if self.parent._focused is self.parent.right_panel:
            if self.parent.right_panel.vertical_split:
                return self.parent.right_panel._get_left()
            else:
                return self.parent.left_panel
        elif self.parent._focused is self.parent.left_panel:
            if self.parent.parent is not self.parent:
                return self.parent.parent.get_left_panel(caller=self)
            else:
                return self.get_left_buffer(caller=self)

    def get_right_buffer(self, caller=None):
        if caller is self:
            return self
        if self.parent._focused is self.parent.left_panel:
            if self.parent.right_panel.vertical_split:
                return self.parent.right_panel._get_right()
            else:
                return self.parent.right_panel
        elif self.parent._focused is self.parent.right_panel:
            if self.parent.parent is not self.parent:
                return self.parent.parent.get_right_panel(caller=self)
            else:
                return self.get_right_buffer(caller=self)

    def _get_right(self):
        """Do not use this. will only work with inside get_right_window()"""
        if self.vertical_split:
            return self.right_panel.get_right_buffer()
        else:
            return self

    def _get_left(self):
        """Do not use this. will only work with inside get_left_window()"""
        if self.vertical_split:
            return self.left_panel.get_left_buffer()
        else:
            return self
            
    def change_buffer(self, new_buffer):
        assert self._v_split_flag is False
        self.buff = new_buffer
        return self
            
    def merge_from_left_panel(self):
        if self._v_split_flag is False:
            return
        else:
            self.buff = self.left_panel.buff
            del self.right_panel
            del self.left_panel
            self._v_split_flag = False
            self._focused = self

    def merge_from_right_panel(self):
        if self._v_split_flag is False:
            return
        else:
            self.buff = self.right_panel.buff
            del self.right_panel
            del self.left_panel
            self._v_split_flag = False
            self._focused = self

    def move_v_split_center(self):
        self.v_split_shift = 0

    def move_v_split_left(self, count=None):
        if count is None:
            count = 1
        new_shift = self.v_split_shift - count
        if new_shift > -self.vertical_split + (self.vertical_split/5):
            self.v_split_shift -= count

    def move_v_split_right(self, count=None):
        if count is None:
            count = 1
        new_shift = self.v_split_shift + count
        if new_shift < ((self.number_of_col * 1.2) - self.vertical_split):
            self.v_split_shift = new_shift

    @property
    def focused(self):
        if self._focused is not self:
            return self._focused.focused
        else:
            return self

    @property
    def number_of_col(self):
        if self is self.parent.left_panel:
            return self.parent.vertical_split - 1    
        elif self is self.parent.right_panel:
            return self.parent.number_of_col - self.parent.vertical_split

    @property
    def number_of_lin(self):
        return self.parent.number_of_lin

    @property
    def vertical_split(self):
        if self._v_split_flag is False:
            return False
        if self.number_of_col % 2 == 0:
            return int((self.number_of_col / 2) + self.v_split_shift)
        return int(((self.number_of_col + 1) / 2) + self.v_split_shift)

    def vsplit(self, right_focus=False):
        if self._v_split_flag is False:
            self._v_split_flag = True
            self.left_panel = Window( self, self.shift_to_col, self.shift_to_lin, self.buff)
            self.right_panel = Window( self, self.shift_to_col, self.shift_to_lin, self.buff)

            if right_focus:
                self.right_panel.set_focus()
            else:
                self.left_panel.set_focus()
        return self._focused

    def gen_window(self):
        if self.vertical_split:
            left_panel = self.left_panel.gen_window()
            right_panel = self.right_panel.gen_window()
            for _ in range(self.number_of_lin):
                yield next(left_panel) + '|' + next(right_panel)

        else:
            max_col = self.number_of_col
            min_lin = self.shift_to_lin
            max_lin = self.number_of_lin + self.shift_to_lin
            cursor_lin, cursor_col = self.buff.cursor_lin_col
            wrap = self.buff.set_wrap
            number = self.buff.set_number
            tab_size = self.buff.set_tabsize
            try:
                for on_lin in range(min_lin, max_lin):
                    index, pretty_line = self.buff.get_lexed_line(on_lin)
                    assert index == on_lin
                    if number:
                        to_print = expandtabs_numbered(tab_size, max_col, pretty_line, on_lin, cursor_lin, cursor_col)
                    else:
                        to_print = expandtabs(tab_size, max_col, pretty_line, on_lin, cursor_lin, cursor_col)
                    if wrap:
                        yield from to_print
                    else: 
                        yield to_print[0]
            except IndexError:
                default = f"{'~':{max_col}}"
                while True:
                    yield default

class Screen(Window):
    def __init__(self, buff):
        self._minibar_flag = 2
        self.buff = buff
        self._v_split_flag = False
        self.v_split_shift = 0
        self._focused = self
        self.parent = self
        self.shift_to_lin = 0
        self.shift_to_col = 0
        self._old_screen = [None for _ in range(MAGIC_VALUE)]
        self._old_term_size = (0, 0)

    def vsplit(self):
        if self.focused != self:
            self.focused.vsplit()
        else:
            super().vsplit().set_focus()
                
    def show(self, renew=False):
        self.hide_cursor()
        curwin = self.focused
        lin, col = curwin.buff.cursor_lin_col
        self.recenter()
#        if lin < curwin.shift_to_lin:
#            curwin.shift_to_lin = lin
#        if lin > curwin.shift_to_lin + curwin.number_of_lin - 1:
#            curwin.shift_to_lin = lin - self.number_of_lin + 1

        self._old_term_size = get_terminal_size()
        for line, index in zip(self.gen_window(), range(1, self.number_of_lin + 1)):
            if self._old_screen[index] != line or renew:
                self.go_line(index)
                stdout.write(line)
                self._old_screen[index] = line
        self.bottom()
        self.show_cursor()
        stdout.flush()

    def recenter(self):
        curwin = self.focused
        lin, col = curwin.buff.cursor_lin_col
        if lin < curwin.shift_to_lin:
            curwin.shift_to_lin = lin
            return
        if lin > curwin.shift_to_lin + curwin.number_of_lin - 1:
            curwin.shift_to_lin = lin - self.number_of_lin + 1

    def minibar(self, txt):
        #self.save_cursor()
        self.bottom()
        self.clear_line()
        if txt.endswith('\n'):
            stdout.write('\x1b[0m\r' + txt[:-1] + '\r' )
        else:
            stdout.write('\x1b[0m\r' + txt + '\r')
        #self.restore_cursor()

    def infobar(self, right='', left=''):
        middle = int(self.number_of_col / 2)

        if len(left) + 5 > middle:
            left = left[:middle - 5] + '....'

        if len(right) + 5 > middle:
            right = right[:middle - 5] + '....'

        right = '\x1b[7m\x1b[1m' + right + '\x1b[0m'

        self.go_line(self.number_of_lin + 1)

        stdout.write(f"\r\x1b[0m{right.ljust(middle, ' ')}{left.rjust(middle, ' ')}")
        self.bottom()

    @staticmethod
    def hide_cursor():
        stdout.write('\x1b[25l')

    @staticmethod
    def show_cursor():
        stdout.write('\x1b[25h')


    @staticmethod
    def insert(text):
#        stdout.write(f'\x1b[@{text}')
        stdout.write(f'\x1b[@\x1b[7m{text}\x1b[27m')
        stdout.flush()

    @staticmethod 
    def clear():
        stdout.write('\x1b\[2J\x1b[09b3J')

    @staticmethod
    def save_cursor():
        stdout.write('\x1b\u009bs')
    
    @staticmethod
    def restore_cursor():
        stdout.write('\x1b8')
    
    @staticmethod
    def top_left():
        stdout.write('\x1b[1;1H')
    
    @staticmethod
    def bottom():
        col, lin = get_terminal_size()
        stdout.write(f'\x1b[{col}H')
    
    @staticmethod
    def bold():
        stdout.write('\x1b[1m')

    @staticmethod
    def go_line(number):
        stdout.write(f'\x1b[{number};1H')

    @staticmethod
    def underline():
        stdout.write('\x1b[4m')

    @staticmethod
    def reversed():
        stdout.write('\x1b[7m')

    @staticmethod
    def clear_line():
        stdout.write('\x1b[2K')
    
    @staticmethod
    def alternative_screen():
        stdout.write('\x1b[?47h')

    @staticmethod
    def original_screen():
        stdout.write('\x1b[?47l')

    @staticmethod
    def clear_screen():
        stdout.write('\x1b[2J')

    @property
    def number_of_col(self):
        columns, lines = get_terminal_size()
        return columns

    @property
    def number_of_lin(self):
        columns, lines = get_terminal_size()
        return lines - self._minibar_flag

    @property
    def needs_redraw(self):
        actual_size = get_terminal_size()
        if actual_size != self._old_term_size:
            return True
        return False
