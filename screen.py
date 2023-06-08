"""
This module is a mess that handles screen rendering.
"""
from os import get_terminal_size
from sys import stdout

from vy.global_config import DEBUG
from vy.utils import Cancel

def expand_quick(max_col, text):
    line = ''
    line = '\x1b[39;22m'
    on_col = 1
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
            line += '\x1b[39;22m'
            return line
#            retval.append(line)
#            line = '\x1b[39;22m'
#            on_col = 1
#            esc_flag = False

        if char == '\t':
            line += ' '
        else:
            line += char
        on_col += 1

    retval.append(line + (' ' * (max_col - on_col)))
    return retval

def expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col, num_len, visual):
    number = f'{on_lin:{num_len}}: '
    line =  f'\x1b[2;37;27m{number}\x1b[39;22m'
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

        if visual_flag and (on_col == start_v): # and on_col == cursor_col:
            line += '\x1b[7m'
            start_cursor = '\x1b[4;5m'
            stop_cursor = '\x1b[24;25m'

        if on_col ==  max_col:
            line += '\x1b[39;22m'
            retval.append(line)
            line = ' ' * len(number)+ '\x1b[39;22m'
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

        if visual and on_col == stop_v:
            line += '\x1b[27m'
            start_cursor = '\x1b[7;5m'
            stop_cursor = '\x1b[27;25m' 

    line += '\x1b[39;22m'
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
        self.make_func = lambda: ([], 0)
        self.view_start = 0

    def __call__(self, make_func):
        self.make_func = make_func 

    def give_up(self):
        return self.__init__()

    def __iter__(self):
        completion, selected = self.make_func()
        if selected != -1:
            pretty_completion = [
                f'| {k} ' if index != selected else f"|\x1b[7m {k} \x1b[27m" 
                       for index, k in enumerate(completion)]
            if selected >= 0:
                if selected <= self.view_start:
                    self.view_start = selected
                if selected > self.view_start + 7:
                    self.view_start = selected - 7
                yield from pretty_completion[self.view_start:self.view_start+8]


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
        self._iter = []
        #self._last = ()
    
    def __iter__(self):
        if self._v_split_flag:
            yield from self.left_panel
        if self._v_split_flag:
            yield from self.right_panel
        else:
            yield self
        
    #def needs_redraw(self):
        #actual = self._last_shown()
        #if self._last != actual:
            #return True
        #return False

    #def __iter__(self):
        #if self.needs_redraw():
            #self._iter = self.gen_window()
        #yield from self._iter

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

    def move_v_split_left(self, count=1):
        new_shift = self.v_split_shift - count
        if new_shift > -self.vertical_split + (self.vertical_split/5):
            self.v_split_shift -= count

    def move_v_split_right(self, count=1):
        new_shift = self.v_split_shift + count
        if new_shift < ((self.number_of_col * 1.2) - self.vertical_split):
            self.v_split_shift = new_shift

    @property
    def focused(self):
        if self._focused is not self:
            return self._focused.focused
        return self

    @property
    def number_of_col(self):
        if self is self.parent.left_panel:
            return self.parent.vertical_split - 1    
        elif self is self.parent.right_panel:
            return self.parent.number_of_col - self.parent.vertical_split

    @property
    def number_of_lin(self):
        return self.parent.number_of_lin - 1

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

    def gen_layout(self, header):
        max_col = self.number_of_col
        min_lin = self.shift_to_lin #+ len(header)
        max_lin = self.number_of_lin + self.shift_to_lin - 1 # For header
        return max_col, min_lin, max_lin

    def gen_accumulator(self):
        notabs = lambda x: expand(tab_size, max_col, pretty_line, on_lin, cursor_lin, cursor_col, num_len, (start_col, stop_col))
        if wrap:
            return lambda xline_list, on_lin, start_col, stop_col: line_list.append(notabs())

    def gen_window(self):
        if self.vertical_split:
            return [f'{left}|{right}' for left, right in zip(
                                            self.left_panel.gen_window(), 
                                            self.right_panel.gen_window())]
        header = expand_quick(self.number_of_col - 8, repr(self.buff)) 
        header = '\x1b[1m**  ' + header[0] + '  **\x1b[22m'

        max_col, min_lin, max_lin = self.gen_layout(header)
        
#        accumulate = self.gen_accumulator(self)
        
        wrap = self.buff.set_wrap
        if (number := self.buff.set_number):
            num_len = len(str(max_lin))
            expand = expandtabs_numbered
        else:
            expand = expandtabs
            num_len = None
        tab_size = self.buff.set_tabsize
        
        true_cursor = 0
        default = f"~{' ':{max_col- 1}}"
        
        cursor_lin, cursor_col, raw_line_list \
                = self.buff.get_raw_screen(min_lin, max_lin)

        line_list = list()
        for on_lin, pretty_line in enumerate(raw_line_list, start=min_lin):
            if pretty_line is None:
                line_list.append(default)
                continue
            if on_lin == cursor_lin and true_cursor == 0:
                true_cursor = len(line_list)
       
            try:
                (start_lin, start_col),(stop_lin, stop_col) = self.buff.selected_lin_col
                if start_lin > on_lin or on_lin > stop_lin:
                    raise TypeError
                start_col = start_col if start_lin == on_lin else -1 
                line_len = len(self.buff.splited_lines[on_lin])
                stop_col = stop_col if stop_lin == on_lin else line_len
            except TypeError:
                start_col = stop_col = 0

            to_print = expand(tab_size, max_col, pretty_line, on_lin, cursor_lin, cursor_col, num_len, (start_col, stop_col))
            if wrap:
                line_list.extend(to_print)
            else:
                line_list.append(to_print[0])

        if wrap:
            while len(line_list) != self.number_of_lin:
                if true_cursor >= self.number_of_lin:
                    line_list.pop(0)
                    true_cursor -= 1
                else:
                    line_list.pop()
        #else:
            #assert len(line_list) == self.number_of_lin - 1 # For header

        #return [header, *line_list]
        return line_list

    def _last_shown(self):
        return (self.number_of_col, 
                self.number_of_lin, 
                self.shift_to_lin, 
                self.shift_to_col,
                self.buff.set_wrap,
                self.buff.set_number,
                self.buff.set_tabsize,
                self.buff.selected_offsets,
                self.buff._string,
                len(self.buff._splited_lines) + len(self.buff._lexed_lines),
                )

class _Screen(Window):
    def __init__(self, buff):
        self.buff = buff
        self._v_split_flag = False
        self.v_split_shift = 0
        self._focused = self
        self.parent = self
        self.shift_to_lin = 0
        self.shift_to_col = 0
        self._infobar_right = ''
        self._infobar_left = ''
        self._minibar_txt = ('',)
        self.minibar_completer = CompletionBanner()

        columns, lines = get_terminal_size()
        self._number_of_col = columns
        self._number_of_lin = lines - len(self.minibar_banner) - 1 # 1 for infobar

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
        columns, lines = get_terminal_size()
        self._number_of_col = columns
        minibar = self.minibar_banner.copy()
        self._number_of_lin = lines - len(minibar)
        curwin = self.focused

        try:
            lin, col = curwin.buff._cursor_lin_col
        except ValueError:
            ok_flag = False
        else:
            if lin < curwin.shift_to_lin:
                curwin.shift_to_lin = lin
            elif lin > curwin.shift_to_lin + curwin.number_of_lin - 1:
                curwin.shift_to_lin = lin - self._number_of_lin + 1
            ok_flag = True

        try:
            rv = self.gen_window()
        except RuntimeError:
            rv = [''] * self._number_of_lin
            ok_flag = False

        rv.extend(minibar)
        return rv, ok_flag

    def minibar(self, *lines):
        self._minibar_txt = lines
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
    def infobar_txt(self):
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
        left =  '\x1b[7;1m' + left + '\x1b[27;22m'
        return f"{left}{right}"

    def hide_cursor(self):
        stdout.write('\x1b[0m\x1b[?25l')

    def show_cursor(self):
        stdout.write('\x1b[?25h')

    def insert(self, text):
        stdout.write(f'\x1b[@\x1b[7m{text}\x1b[27m')
        stdout.flush()

    def clear(self):
        stdout.write('\x1b[2J\x1b[09b3J')

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
        
class _DebugScreen(_Screen):
    @property
    def minibar_banner(self):
        from time import sleep
        
        from vy.global_config import USER_DIR
        from pprint import pformat
        from __main__ import Editor
#                from time import asctime
        debug_file = USER_DIR / "debugging_values"
        to_print = '\x1b[04m ' * (self.number_of_col - 1) + '\x1b[0m\n'
        for line in debug_file.read_text().splitlines():
            if line:
                try:
                    value = pformat(eval(line))
                    to_print += f'\x1b[2m{line}\x1b[0m = {value} \n'
                except BaseException as exc:
                    value = str(exc)
                    to_print += f'\x1b[35;1m{line}\n     <<< ___ERROR____ >>>\n{value}\x1b[0m'
        rv = list()
        for line in to_print.splitlines():
            rv.extend(expand_quick(self.number_of_col, line))
        rv.append(self.infobar_txt)
        for line in self.minibar_completer:
            rv.extend(expand_quick(self.number_of_col, line))
        for line in self._minibar_txt:
            rv.extend(expand_quick(self.number_of_col, line))
#                rv.extend(expandtabs(3, self.number_of_col , str(asctime()), 1, 0, 0, None, None))
        return rv

if DEBUG:
    Screen = DebugScreen
else:
    Screen = _Screen
