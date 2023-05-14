"""
This module is a mess that handles screen rendering.
"""

from os import get_terminal_size
from sys import stdout

from vy.global_config import DEBUG

def expand_quick(max_col, text):
    line = ''
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
            line += '\x1b[39;49m'
            retval.append(line)
            line = '\x1b[39;49m'
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
    #assert '/n' not in text
    number = f'{on_lin:{num_len}}: '
    line =  f'\x1b[00;90;40m{number}\x1b[39;49m'
    start_cursor = '\x1b[5;7m'
    stop_cursor = '\x1b[25;27m'
    retval: list = list()
    on_col: int = len(number)
    cursor_col += on_col - 1
    esc_flag: bool = False
    cursor_flag: bool = cursor_lin == on_lin
    cursor_char_flag = False

    if visual:
        start_v, stop_v = visual
        visual = bool(visual)
        start_v += on_col - 1
        stop_v += on_col - 1
#        if stop_v == start_v:
#            visual = False

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

        if visual and on_col == start_v: # and on_col == cursor_col:
            line += '\x1b[7m'
            start_cursor = '\x1b[27;5;4m'
            stop_cursor = '\x1b[7;25;24m'

        if on_col ==  max_col:
            line += '\x1b[39;49m'
            retval.append(line)
            line = '\x1b[90;40m' + ' ' * len(number)+ '\x1b[39;49m'
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

        if visual and on_col == stop_v + 1:
            line += '\x1b[22;25;27m'

    retval.append(line + (' ' * (max_col - on_col)))
    return retval

#@cache
def expandtabs(tab_size, max_col, text, on_lin, cursor_lin, cursor_col, num_len, visual):
    #assert '/n' not in text
    retval: list = list()
    line: str = '\x1b[00;39;49m'
    start_cursor = '\x1b[5;7m'
    stop_cursor = '\x1b[25;27m'
    on_col: int = 1
    cursor_col += on_col - 1
    esc_flag: bool = False
    cursor_flag: bool = False

    if visual:
        start_v, stop_v = visual
        visual = bool(visual)
        start_v += on_col - 1
        stop_v += on_col - 1
#        if stop_v == start_v:
#            visual = False

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

        if visual and on_col == start_v: # and on_col == cursor_col:
                line += '\x1b[7m'
                start_cursor = '\x1b[27;5;4m'
                stop_cursor = '\x1b[7;25;24m'

        if on_col ==  max_col:
            line += '\x1b[39;49m'
            retval.append(line)
            line = '\x1b[39;49m'
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
            line += '\x1b[22;25;27m'

    retval.append(line + (' ' * (max_col - on_col)))
    return retval

class CompletionBanner:
    def __init__(self):
        self.view_start = 0
        self.max_selected = -1
        self.selected = -1
        self.completion = []
        self.pretty_completion = []
        self.prefix_len = 0
        self.check_func = lambda: False
        self.make_func = lambda: ([], 0)
        self._active = False

    def set_callbacks(self, make_func, check_func):
        self.make_func = make_func
        self.check_func = check_func
        self.generate()

    def generate(self):
        try:
            self.completion, self.prefix_len = self.make_func()
        except TypeError: #Jedi-completer returned None
            return self.give_up()
        if self.completion:
            self.selected = 0
            self.view_start = 0
            self.max_selected = len(self.completion) - 1
            self._active = True
            self._update()
        else:
            self.give_up()
    
    def give_up(self):
        self.__init__()

    def __iter__(self):
        if self.check_func():
            self.generate()
        yield from self.pretty_completion[self.view_start:self.view_start+8]

    def __bool__(self):
        return self._active #and self.selected > 0

    def move_cursor_up(self):
        if self.selected > 0:
            self.selected -= 1
        else:
            self.selected = self.max_selected
        self._update()

    def move_cursor_down(self):
        if self.selected == self.max_selected:
            self.selected = 0
        else:
            self.selected += 1
        self._update()

    def _update(self):
        self.pretty_completion = [
            f'| {k} ' if index != self.selected else f"|\x1b[7m {k} \x1b[27m" 
                   for index, k in enumerate(self.completion)]
        if self.selected <= self.view_start:
            self.view_start = self.selected
        if self.selected > self.view_start + 7:
            self.view_start = self.selected - 7

    def select_item(self):
        if self.completion:
            return self.completion[self.selected], self.prefix_len
        return '', 0

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
        self._last = ()
    
    def __iter__(self):
        if self._v_split_flag:
            yield from self.left_panel
        if self._v_split_flag:
            yield from self.right_panel
        else:
            yield self
        
    def needs_redraw(self):
        actual = self._last_shown()
        if self._last != actual:
            return True
        return False

    #def __iter__(self):
        #if self.needs_redraw():
            #self._iter = self.gen_window()
        #yield from self._iter

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
            if not self.right_panel.needs_redraw() and not self.left_panel.needs_redraw():
                return [f'{left}|{right}' for left, right in zip(
                                            self.left_panel._last_computed,
                                            self.right_panel._last_computed)]
                
            return [f'{left}|{right}' for left, right in zip(
                                            self.left_panel.gen_window(), 
                                            self.right_panel.gen_window())]
#        if not self.needs_redraw():
#            return self._last_computed
           
        max_col = self.number_of_col
        min_lin = self.shift_to_lin
        max_lin = self.number_of_lin + self.shift_to_lin
        wrap = self.buff.set_wrap
        if (number := self.buff.set_number):
            num_len = len(str(max_lin))
            expand = expandtabs_numbered
        else:
            expand = expandtabs
            num_len = None
        tab_size = self.buff.set_tabsize
        default = f"~{' ':{max_col- 1}}"
        true_cursor = 0
        visual = self.buff.selected_lin_col
        
        cursor_lin, cursor_col, raw_line_list \
                = self.buff.get_raw_screen(min_lin, max_lin)

        line_list = list()
        for on_lin, pretty_line in enumerate(raw_line_list, start=min_lin):
            if pretty_line is None:
                line_list.append(default)
                continue
            if on_lin == cursor_lin and true_cursor == 0:
                true_cursor = len(line_list)
       
            if visual and (visual := on_lin in self.buff.selected_lines):
                (start_lin, start_col),(stop_lin, stop_col) = self.buff.selected_lin_col
                if on_lin != start_lin:
                    start_col = 1
                if on_lin != stop_lin:
                    stop_col = -1
                visual = (start_col, stop_col)

            to_print = expand(tab_size, max_col, pretty_line, on_lin, cursor_lin, cursor_col, num_len, visual)
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

        self._last = self._last_shown()
        self._last_computed = line_list
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

class Screen(Window):
    def __init__(self, buff):
        self._last = None
        self.buff = buff
        self._v_split_flag = False
        self.v_split_shift = 0
        self._focused = self
        self.parent = self
        self.shift_to_lin = 0
        self.shift_to_col = 0
        self._infobar_right = ''
        self._infobar_left = ''
        self._minibar_txt = ['']
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
            rv = self.gen_window().copy()
        except RuntimeError:
            rv = [''] * self._number_of_lin
            ok_flag = False
        except BaseException as exc:
            rv = [str(exc), '', '']
            ok_flag = False
        rv.extend(self.minibar_banner)
        return rv, ok_flag

    def minibar(self, *lines):
        self._minibar_txt.clear()
        self._minibar_txt.extend(lines)
        copy = self._minibar_txt.copy()
        return lambda: (self._minibar_txt.clear(),
                        self._minibar_txt.append('')) if self._minibar_txt == copy else None
    
    if DEBUG:
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
    else:
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
        left = '\x1b[7m\x1b[1m' + left + '\x1b[0m'
        return f"{left}{right}"

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
        
def _tests():
    test_str = '01234567890\x1b[1m234567890'
    
