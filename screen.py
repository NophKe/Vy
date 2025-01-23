"""
This module is a mess that handles screen rendering.
"""

from os import get_terminal_size
from sys import stdout

from vy.global_config import DEBUG  

def expand_quick(max_col, text):
    if not text:
        return [ ' ' * max_col ]
    line = ''
    line = '\x1b[97;22m'
    on_col = 0
    retval = []
    esc_flag: bool = False
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
            line += '\x1b[97;22m'
            retval.append(line)
            line = '\x1b[97;22m'
            on_col = 1
            esc_flag = False

        if char == '\t':
            line += ' '
        else:
            line += char
        on_col += 1

    retval.append(line + (' ' * (max_col - on_col)))
    return retval


def expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col, num_len, visual):
    number = f'{on_lin:{num_len}}: '
    line =  f'\x1b[2;37;27m{number}\x1b[97;22m'
    start_cursor = '\x1b[7;5m'
    stop_cursor = '\x1b[27;25m'
    retval: list = list()
    on_col: int = len(number)
    cursor_col += on_col - 1
    esc_flag: bool = False
    cursor_flag: bool = cursor_lin == on_lin
    cursor_char_flag = False

    visual_flag = any(visual)
    start_v, stop_v = visual

    if visual_flag:
        if start_v == -1:
            start_v = on_col
        else:
            start_v += on_col - 1
        if stop_v != -1:
            stop_v += on_col 

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

        if visual_flag and (on_col == start_v): # and on_col == cursor_col:
            line += '\x1b[7m'
            start_cursor = '\x1b[27;4;5m'
            stop_cursor = '\x1b[7;24;25m'

        if on_col ==  max_col:
            line += '\x1b[97;22m'
            retval.append(line)
            line = ' ' * len(number)+ '\x1b[97;22m'
            cursor_col  = cursor_col - (max_col - len(number))
            on_col = len(number)
            esc_flag = False

        if cursor_flag and on_col == cursor_col:
            cursor_char_flag = True
            line += start_cursor

        if char == '\t':
            nb_of_tabs =  tab_size - ((on_col - len(number)) % tab_size)
            line += ' ' * nb_of_tabs
            on_col += nb_of_tabs
            cursor_col += (nb_of_tabs-1)
        else:
            on_col += 1
            line += char


        if cursor_char_flag:
            cursor_char_flag = False
            line += stop_cursor

        if visual_flag and on_col == stop_v:
            line += '\x1b[27m'
            start_cursor = '\x1b[7;5m'
            stop_cursor = '\x1b[27;25m' 

    line += '\x1b[97;22m'
    if stop_v == -1:
        line += '\x1b[27m'

    retval.append(line + (' ' * (max_col - on_col)))
    return retval

def expandtabs(tab_size, max_col, text, on_lin, cursor_lin, cursor_col, num_len, visual):
    retval: list = list()
    line: str = '\x1b[49m'
    start_cursor = '\x1b[5;7m'
    stop_cursor = '\x1b[25;27m'
    on_col: int = 1
    cursor_col += on_col - 1
    esc_flag: bool = False
    cursor_flag: bool = False

    visual_flag = any(visual)
    start_v, stop_v = visual
    if start_v:
        if start_v == -1:
            line += '\x1b[7m'
        else:
            start_v += on_col - 1
    if stop_v:
        stop_v += on_col 

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

        if visual and on_col == start_v:
            line += '\x1b[7m'
            start_cursor = '\x1b[4;5m'
            stop_cursor = '\x1b[24;25m'

        if on_col ==  max_col:
            line += '\x1b[49m'
            retval.append(line)
            line = '\x1b[49m'
            cursor_col  = cursor_col - max_col + 1
            on_col = 1
            esc_flag = False

        cursor_flag = on_col == cursor_col and on_lin == cursor_lin
        if cursor_flag:
            line += start_cursor

        if char == '\t':
            nb_of_tabs =  tab_size - (on_col % tab_size)
            line += ' ' * nb_of_tabs
            on_col += nb_of_tabs
            cursor_col += (nb_of_tabs-1)
        else:
            on_col += 1
            line += char
        if cursor_flag:
            line += stop_cursor

        if visual and on_col == stop_v + 1:
            line += '\x1b[22;25m'

    retval.append(line + (' ' * (max_col - on_col)))
    return retval

class CompletionBanner:
    def __init__(self):
        self.view_start = 0
        self.pretty_completion = []
        self.make_func = lambda: ([], -1)
        self.selected = -1
        self.pretty_completion = []
        self.completion = []

    def set_value(self, completion, selected):
        self.completion = completion
        self.selected = selected

    def __call__(self, make_func):
        self.set_value(*make_func())

    def give_up(self):
        self.__init__()

    def __iter__(self):
#        self.completion, self.selected = self.make_func()
        if self.completion: # and self.selected != -1:
            self.pretty_completion = [
                f'| {k} ' if index != self.selected else f">\x1b[7m {k} \x1b[27m" 
                       for index, k in enumerate(self.completion)]
            if self.selected >= 0:
                if self.selected <= self.view_start:
                    self.view_start = self.selected
                if self.selected > self.view_start + 7:
                    self.view_start = self.selected - 7
            yield from self.pretty_completion[self.view_start:self.view_start+8]


class Window():
    def __iter__(self):
        if self._v_split_flag:
            yield from self.left_panel
            yield from self.right_panel
        else:
            yield self

    def set_focus(self):
        if self.parent is not self:
            if self.parent._focused is not self:
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
        # TODO may be shorter
        self.buff = new_buffer
        cursor_line = new_buffer.current_line_idx
        maxline = new_buffer.number_of_lin
        halfscreen = self.number_of_lin // 2
        max_shift = maxline - halfscreen
        new_shift = cursor_line - halfscreen
        self.shift_to_lin = min(maxline, max(0, new_shift))
        return self

    def merge_from_left_panel(self):
        if self._v_split_flag:
            self.buff = self.left_panel.buff
            self.right_panel = self.left_panel = None
            self._v_split_flag = False
            self._focused = self

    def merge_from_right_panel(self):
        if self._v_split_flag:
            self.buff = self.right_panel.buff
            self.right_panel = self.left_panel = None
            self._v_split_flag = False
            self._focused = self

    def move_v_split_center(self):
        self.v_split_shift = 0

    def move_v_split_left(self, count=1):
        new_shift = self.v_split_shift - count
        if new_shift > -self.vertical_split + (self.vertical_split / 5):
            self.v_split_shift -= count

    def move_v_split_right(self, count=1):
        new_shift = self.v_split_shift + count
        if new_shift < ((self.number_of_col * 1.2) - self.vertical_split):
            self.v_split_shift = new_shift

    @property
    def focused(self):
        return self._focused.focused if self._focused is not self else self

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
        return ((self.number_of_col + 1) // 2) + self.v_split_shift

    def vsplit(self, right_focus=False):
        assert not self._v_split_flag
        self._v_split_flag = True
        self.left_panel = Window(self, self.shift_to_col, self.shift_to_lin, self.buff)
        self.right_panel = Window(self, self.shift_to_col, self.shift_to_lin, self.buff)
        self.right_panel.set_focus() if right_focus else self.left_panel.set_focus()

        return self._focused

    def gen_window(self):
        if self.vertical_split:
            return [f'{left}|{right}' for left, right in zip(
                                            self.left_panel.gen_window(), 
                                            self.right_panel.gen_window())]
        header = self.gen_header()
        footer = self.gen_footer()

        number_of_lines = self.number_of_lin - len(footer) - len(header)
        min_lin = self.shift_to_lin
        max_lin = number_of_lines + self.shift_to_lin
        self.shown_lines = (min_lin, max_lin)

        header.extend(self.gen_body(min_lin, max_lin))
        header.extend(footer)
        return header

    def gen_header(self):
        if self.parent.focused is self:
            head_line = '\x1b[1;7m' + self.buff.header + '\x1b[22;27m'
        else:
            head_line = '\x1b[02m' + self.buff.header + '\x1b[22;27m'
        return expand_quick(self.number_of_col, head_line)

    def gen_footer(self):
        return expand_quick(self.number_of_col, self.buff.footer)

    def gen_body(self, min_lin, max_lin):
        max_col = self.number_of_col
        wrap = self.buff.set_wrap
        if number := self.buff.set_number:
            num_len = len(str(max_lin))
            expand = expandtabs_numbered
        else:
            expand = expandtabs
            num_len = None
        tab_size = self.buff.set_tabsize

        default = f"~{' ':{max_col- 1}}"
        true_cursor = 0

        try:
            (start_lin, start_col), (stop_lin, stop_col) = self.buff.selected_lin_col
        except TypeError:
            start_col = stop_col = 0
            start_lin = stop_lin = -1

        cursor_lin, cursor_col, raw_line_list = self.buff.get_raw_screen(min_lin, max_lin)

        line_list = list()
        for on_lin, pretty_line in enumerate(raw_line_list, start=min_lin):
            if pretty_line is None:
                line_list.append(default)
                continue

            if on_lin == cursor_lin and true_cursor == 0:
                true_cursor = min_lin + len(line_list)

            if start_lin <= on_lin <= stop_lin:
                if start_lin != on_lin:
                    start_v_col = -1
                else:
                    start_v_col = start_col
                if stop_lin != on_lin:
                    stop_v_col = -1
                else:
                    stop_v_col = stop_col
            else:
                start_v_col = stop_v_col = 0

            to_print = expand(
                tab_size, max_col, pretty_line, on_lin, cursor_lin,
                cursor_col, num_len, (start_v_col, stop_v_col)
            )
            if wrap:
                line_list.extend(to_print)
            else:
                line_list.append(to_print[0])

        if wrap:
            shown_lines =  max_lin - min_lin
            # TODO some wher in this lies the bug
            while len(line_list) != shown_lines:
                try:
                    if true_cursor >= max_lin:
                        line_list.pop(0)
                        true_cursor -= 1
                    else:
                        line_list.pop()
                except IndexError:
                    raise RuntimeError
                    assert true_cursor, f'{true_cursor = }'
                    assert line_list, f'{line_list = }'
                    assert shown_lines, f'{shown_lines = }'
                    assert cursor_col, f'{cursor_col = }'
                    assert cursor_lin, f'{cursor_lin = }'
                    raise

        return line_list

    def __init__(self, parent, shift_to_col, shift_to_lin, buff):
        self.parent = parent
        self.shift_to_col = shift_to_col
        self.shift_to_lin = shift_to_lin
        self.buff = buff

        self.left_panel = None
        self.right_panel = None
        self._v_split_flag = False
        self.v_split_shift = 0
        self._focused = self
        self.shown_lines = (0, 0)


class Screen(Window):
    def __init__(self, buff):
        super().__init__(self, 0, 0, buff)

        self._infobar_right = ''
        self._infobar_left = ''
        self._minibar_txt = ('',)
        self.minibar_completer = CompletionBanner()

        columns, lines = get_terminal_size()
        self._number_of_col = columns
        self._number_of_lin = lines - len(self.minibar_banner)  # 1 for infobar
        self.shown_lines = (0, 0)

    def vsplit(self):
        if self.focused != self:
            self.focused.vsplit()
        else:
            super().vsplit().set_focus()

    @property
    def number_of_col(self):
        return self._number_of_col

    @property
    def number_of_lin(self):
        return self._number_of_lin

    def get_line_list(self):
        minibar = self.minibar_banner

        columns, lines = get_terminal_size()
        self._number_of_col = columns
        self._number_of_lin = lines - len(minibar)

        try:
            rv = self.gen_window()
        except RuntimeError as exc:
            #raise
            rv = [''] * self._number_of_lin
            ok_flag = False
            error = str(exc)
        else:
            ok_flag = True
            error = ''

        rv.extend(minibar)
        return rv, ok_flag, error

    def minibar(self, *lines):
#        assert all(line.isprintable() for line in lines)
        if lines:
            self._minibar_txt = lines
        else:
            self._minibar_txt = ('',)
        return lambda: self.minibar('') if self._minibar_txt == lines else None
    
    @property
    def minibar_banner(self):
        rv = list()
        for line in self.minibar_completer:
            rv.extend(expand_quick(self.number_of_col, line))
        rv.append(self.infobar_txt)
        for line in self._minibar_txt:
            rv.extend(expand_quick(self.number_of_col, line))
        return rv

    def infobar(self, left='', right=''):
        self._infobar_left = left
        self._infobar_right = right

    @property
    def infobar_txt(self, ns={}):
        left = self._infobar_left
        right = self._infobar_right
        middle = self.number_of_col // 2
        if len(right) + 5 > middle:
            right = right[:middle - 5] + '....'
        else:
            right = right.rjust(middle, ' ')
        if len(left) + 5 > middle:
            left = left[:middle - 5] + '....'
        else:
            left = left.ljust(middle, ' ')
        return f'\x1b[7;1m{left}\x1b[27;22m{right}'
    
    def recenter(self):
        curwin = self.focused
        curbuf = self.focused.buff


        min_lin, max_lin = curwin.shown_lines
        if max_lin: # gen_windows() allready got called once
            try:
                lin, col = curbuf._cursor_lin_col
            except ValueError: #buffer in inconsisant state
                return
                if curbuf._async_tasks.must_stop:
                    raise RuntimeError('recenter should wait')
                lin, col = curbuf.cursor_lin_col
            if lin not in range(min_lin, max_lin):
                if lin < min_lin:
                    curwin.shift_to_lin = lin
                elif lin >= max_lin:
                    page_size = max_lin - min_lin - 1
                    curwin.shift_to_lin = lin - page_size 

    def hide_cursor(self):
        stdout.write('\x1b[?25l')

    def show_cursor(self):
        stdout.write('\x1b[?25h')

    def insert(self, text):
        stdout.write(f'\x1b[@\x1b[7m{text}\x1b[27m')
        stdout.flush()

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
        stdout.write('\x1b[1J')
        stdout.write('\x1b[2J')
        stdout.write('\x1b[3J')

    def enable_bracketed_paste(self):
        stdout.write('\x1b[?2004h')

    def disable_bracketed_paste(self):
        stdout.write('\x1b[?2004l')

    def reset(self):
       print('\x1b[0m', flush=True, end='')

    def enable_mouse_tracking(self):
        stdout.write('\x1b[?9h')
#        stdout.write('\x1b[?1000h')

    def disable_mouse_tracking(self):
        stdout.write('\x1b[?9l')
#        stdout.write('\x1b[?1000l')
