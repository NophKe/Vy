"""This module is a mess that handles screen rendering"""
from os import get_terminal_size
from sys import stdout

def get_rows_needed(number):
    if number < 800: return 3
    elif number < 9800: return 4
    elif number < 99800: return 5
    elif number < 999800: return 6
    return len(str(number))

def expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
    #assert '/n' not in text
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

        cursor_flag = on_col == cursor_col and on_lin == cursor_lin
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
    #assert '/n' not in text
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

        cursor_flag = on_col == cursor_col and on_lin == cursor_lin
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
        self.left_panel = None
        self.right_panel = None
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
            self.right_panel = self.left_panel = None
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
            rv = list()
            for _ in range(self.number_of_lin):
                rv.append(next(left_panel) + '|' + next(right_panel))
            return rv

        else:
            max_col = self.number_of_col
            min_lin = self.shift_to_lin
            max_lin = self.number_of_lin + self.shift_to_lin
            cursor_lin, cursor_col = self.buff.cursor_lin_col
            wrap = self.buff.set_wrap
            number = self.buff.set_number
            tab_size = self.buff.set_tabsize
            default = f"~{' ':{max_col- 1}}"
            true_cursor = 0

            line_list = list()
            for on_lin in range(min_lin, max_lin):
                if on_lin == cursor_lin and true_cursor == 0:
                    true_cursor = len(line_list)
                try:
                    pretty_line = self.buff.get_lexed_line(on_lin)
                except IndexError:
                    line_list.append(default)
                    continue
                if number:
                    to_print = expandtabs_numbered(tab_size, max_col, pretty_line, on_lin, cursor_lin, cursor_col)
                else:
                    to_print = expandtabs(tab_size, max_col, pretty_line, on_lin, cursor_lin, cursor_col)
                if wrap:
                    line_list.extend(to_print)
                else:
                    line_list.append(to_print[0])
            if true_cursor >= self.number_of_lin:
                to_remove = 1 + true_cursor - self.number_of_lin
                line_list = line_list[to_remove:]
            return line_list 
            #yield from line_list

class Screen(Window):
    def __init__(self, buff):
        self.buff = buff
        self._v_split_flag = False
        self.v_split_shift = 0
        self._focused = self
        self.parent = self
        self.shift_to_lin = 0
        self.shift_to_col = 0
        self._infobar_txt = ''
        self._minibar_txt = ['']
        self._minibar_completer = []
        self.recenter()

    def vsplit(self):
        if self.focused != self:
            self.focused.vsplit()
        else:
            super().vsplit().set_focus()

    def recenter(self):
        columns, lines = get_terminal_size()
        self._number_of_col = columns
        self._number_of_lin = lines - len(self.minibar_banner) - 1 # 1 for infobar
        curwin = self.focused
        lin, col = curwin.buff.cursor_lin_col
        if lin < curwin.shift_to_lin:
            curwin.shift_to_lin = lin
        elif lin > curwin.shift_to_lin + curwin.number_of_lin - 1:
            curwin.shift_to_lin = lin - self.number_of_lin + 1

    @property
    def number_of_col(self):
        return self._number_of_col

    @property
    def number_of_lin(self):
        return self._number_of_lin

    def get_line_list(self):
        self.recenter()
        rv = self.gen_window()
        rv.append(self._infobar_txt)
        rv.extend(self.minibar_banner)
        return rv 

    def minibar_completer(self, *lines):
        self._minibar_completer.clear()
        self._minibar_completer.extend(lines)

    def minibar(self, *lines):
        self._minibar_txt.clear()
        self._minibar_txt.extend(lines)

    @property
    def minibar_banner(self):
        rv = list()
        for line in self._minibar_completer:
            rv.extend(expandtabs(3, self.number_of_col , line, 1, 0, 0))
        for line in self._minibar_txt:
            rv.extend(expandtabs(3, self.number_of_col , line, 1, 0, 0))
        return rv

    def infobar(self, left='', right=''):
        middle = int(self.number_of_col / 2)
        if len(right) + 5 > middle:
            right = right[:middle - 5] + '....'
        else:
            right = right.rjust(middle, ' ')
        if len(left) + 5 > middle:
            left = left[:middle - 5] + '....'
        else:
            left = left.ljust(middle, ' ')
        left = '\x1b[7m\x1b[1m' + left + '\x1b[0m'
        self._infobar_txt = f"{left}{right}"

    def hide_cursor(self):
        stdout.write('\x1b[0m\x1b[?25l')

    def show_cursor(self):
        stdout.write('\x1b[?25h')

    def insert(self, text):
        stdout.write(f'\x1b[@\x1b[7m{text}\x1b[27m')
        stdout.flush()

    def clear(self):
        stdout.write('\x1b\[2J\x1b[09b3J')

    def save_cursor(self):
        stdout.write('\x1b\u009bs')
    
    def restore_cursor(self):
        stdout.write('\x1b8')
    
    def top_left(self):
        stdout.write('\x1b[1;1H')
    
    def bottom(self):
        col, _ = get_terminal_size()
        stdout.write(f'\x1b[{col}H')
    
    def bold(self):
        stdout.write('\x1b[1m')

    def go_line(self, number):
        stdout.write(f'\x1b[{number};1H')

    def underline(self):
        stdout.write('\x1b[4m')

    def reversed(self):
        stdout.write('\x1b[7m')

    def clear_line(self):
        stdout.write('\x1b[2K')
    
    def alternative_screen(self):
        stdout.write('\x1b[?47h')

    def original_screen(self):
        stdout.write('\x1b[?47l')

    def clear_screen(self):
        stdout.write('\x1b[2J')
