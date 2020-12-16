from os import get_terminal_size
from sys import stdout
from itertools import chain, repeat

from pygments.token import Keyword, Name, Comment, String, Error, Number, Operator, Generic, Token, Whitespace
from pygments.console import ansiformat
from pygments.lexers import guess_lexer_for_filename
from pygments.util import  ClassNotFound

cdef dict colorscheme

colorscheme = {
    Token:              '',
    Whitespace:         'gray',         Comment:            'gray',
    Comment.Preproc:    'cyan',         Keyword:            '*blue*',
    Keyword.Type:       'cyan',         Operator.Word:      'magenta',
    Name.Builtin:       'cyan',         Name.Function:      'green',
    Name.Namespace:     '_cyan_',       Name.Class:         '_green_',
    Name.Exception:     'cyan',         Name.Decorator:     'brightblack',
    Name.Variable:      'red',          Name.Constant:      'red',
    Name.Attribute:     'cyan',         Name.Tag:           'brightblue',
    String:             'yellow',       Number:             'blue',
    Generic.Deleted:    'brightred',
    Generic.Inserted:   'green',        Generic.Heading:    '**',
    Generic.Subheading: '*magenta*',    Generic.Prompt:     '**',
    Generic.Error:      'brightred',    Error:              '_brightred_',
}

cdef object _colorize(object ttype):
    def func(text):
        return ansiformat(color, text)
    for token_class in reversed(ttype.split()):
        if ttype in colorscheme:
            color = colorscheme[ttype]
        else:
            ttype = ttype.parent
    return func

cdef str expandtabs(int tab_size, int max_col, str text):
    cdef:
        list rv = []
        #object rv = list()
        int on_col = 0
        bint esc_flag = False
        str char

    for char in text:
        if on_col ==  max_col :
            rv.append('\x1b[0m')
            return ''.join(rv)
            
        if char == '\x1b':
            esc_flag = True
            rv.append(char)
            continue
        elif esc_flag  and char == 'm': 
            esc_flag = False
            rv.append(char)
            continue
        elif char == '\t':
            nb_of_tabs =  tab_size - (on_col % tab_size)
            rv.append(' ' * nb_of_tabs)
            on_col += nb_of_tabs
        else:
            if not esc_flag:
                on_col += 1
            rv.append(char)

    return ''.join(rv) + (' ' * (max_col - on_col))

def gen_lexed_line(object buff, int max_col, int min_lin):
    if not buff.lexer:
        filename = buff.path if buff.path else ''
        try:
            buff.lexer = guess_lexer_for_filename(filename, buff.getvalue(), tabsize = buff.tab_size, encoding='utf-8')
        except ClassNotFound:
            buff.lexer = guess_lexer_for_filename('text.txt', buff.getvalue(), tabsize = buff.tab_size, encoding='utf-8')

    cdef:
        int chars_to_print = 0
        str line = ''
        int on_lin = 0
        int offset
        object tok
        str val
        bint nl_flag
        int len_to_add
        int cur_pos
        str token_line
        int cursor
        int tab_size = buff.tab_size
    
#    chars_to_print = 0
#    line = ''
#    on_lin = 0
#    tab_size = buff.tab_size
    
    for offset, tok, val in buff.lexer.get_tokens_unprocessed(buff._string):
        colorize = _colorize(tok)

        for token_line in val.splitlines(True):
            nl_flag = token_line.endswith('\n')
            if nl_flag:
                token_line = token_line[:-1] + ' '

            len_to_add = len(token_line)
            cursor = buff.cursor
            
            if (offset + len_to_add) >= cursor >= offset:
                cur_pos = (cursor - offset)
                if cur_pos > len_to_add :
                    token_line = token_line[:cur_pos] + '\x1b7\x1b[7;5m \x1b[25;27m'
                elif cur_pos < len_to_add:
                    token_line = token_line[:cur_pos] + '\x1b7\x1b[7;5m' + token_line[cur_pos] + '\x1b[25;27m' + token_line[cur_pos+1:]

            if nl_flag:
                if on_lin  < min_lin:
                    yield ''
                else:
                    yield expandtabs(tab_size, max_col, line + colorize(token_line) )
                on_lin += 1
                chars_to_print = 0
                line = ''
                offset += len_to_add + chars_to_print
                continue
            elif chars_to_print > max_col:
                continue
            else:
                line += colorize(token_line)
                chars_to_print += len_to_add
                continue
    else:
        if line:
            yield expandtabs(tab_size, max_col, line )

def gen_window_line(buff, int col_shift, int max_col, int lin_shift, int max_lin):
    cdef:
        int max_index
        str item

    max_index = max_lin + lin_shift
    
    for index, item in enumerate(chain(gen_lexed_line(buff, max_col, lin_shift),
                                       repeat( '~'+(' '*(max_col-1))))):
        if index < lin_shift:
            continue
        elif lin_shift <= index <= max_index:
            yield item
        elif index > max_index:
            break


class Window:
    def __init__(self, parent, shift_to_col, shift_to_lin, buff):
        self.parent = parent
        self.shift_to_col = shift_to_col
        self.shift_to_lin = shift_to_lin
        self.buff = buff
        self._v_split_flag = False
        self.v_split_shift = 0
        self._focused = self 

    def set_focus(self):
        if self.parent is self:
            return
        elif self.parent._focused is not self:
            self.parent._focused = self
        self.parent.set_focus()

    def get_left_buffer(self):
        if self.parent._focused is self.parent.right_panel:
            if self.parent.right_panel.vertical_split:
                return self.parent.right_panel._get_left()
            else:
                return self.parent.left_panel
        elif self.parent._focused is self.parent.left_panel:
            if self.parent.parent is not self.parent:
                return self.parent.parent.get_left_panel()
            else:
                return self.get_left_buffer()

    def get_right_buffer(self):
        if self.parent._focused is self.parent.left_panel:
            if self.parent.right_panel.vertical_split:
                return self.parent.right_panel._get_right()
            else:
                return self.parent.right_panel
        elif self.parent._focused is self.parent.right_panel:
            if self.parent.parent is not self.parent:
                return self.parent.parent.get_right_panel()
            else:
                return self.get_right_buffer()

    def _get_right(self):
        """Do not use this. will only work with inside get_right_window()"""
        if self.vertical_split:
            return self.right_panel.get_right_buffer()
        else:
            return self
#
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
        else:
            if self.number_of_col % 2 == 0:
                return int((self.number_of_col / 2) + self.v_split_shift)
            else:
                return int(((self.number_of_col + 1) / 2) + self.v_split_shift)

    def vsplit(self, right_focus=False):
        if self._v_split_flag is False:
            self._v_split_flag = True
            self.left_panel = Window( self, 
                                        self.shift_to_col, 
                                        self.shift_to_lin,
                                        self.buff)

            self.right_panel = Window( self,
                                        self.shift_to_col,
                                        self.shift_to_lin,
                                        self.buff)
            if right_focus:
                self.right_panel.set_focus()
            else:
                self.left_panel.set_focus()
        return self._focused

    def gen_window(self):
        if self.vertical_split:
            left_panel = self.left_panel.gen_window()
            right_panel = self.right_panel.gen_window()
            
            for _ in range(self.number_of_lin ):
                yield next(left_panel) + '|' + next(right_panel)

        else:
            yield from gen_window_line(self.buff,
                                        self.shift_to_col,
                                        self.number_of_col,
                                        self.shift_to_lin,
                                        self.number_of_lin)
 

class Screen(Window):
    def __init__(self, buff, minibar=1):
        self._minibar_flag = minibar
        self.buff = buff
        self._v_split_flag = False
        self.v_split_shift = 0
        self._focused = self
        self.parent = self
        self.shift_to_lin = 0
        self.shift_to_col = 0
        # I assume noone has a screen longer than 100 lines
        self._old_screen = list(' ' * 100)
 
    def vsplit(self):
        if self.focused != self:
            self.focused.vsplit()
        else:
            super().vsplit().set_focus()

    def show(self, bint renew=False):
        self.top_left()
        self.recenter()
        cdef:
            int index
            str line

        for index, line in enumerate(self.gen_window(), start=1):
            if self._old_screen[index] != line or renew:
                self.go_line(index)
                stdout.write(line)
                self._old_screen[index] = line

    def recenter(self):
        cdef:
            object curwin = self.focused
            int lin
            int col

        lin, col = curwin.buff.cursor_lin_col
        if lin < curwin.shift_to_lin + 1:
            curwin.shift_to_lin = lin - 1
        elif lin >= curwin.number_of_lin + curwin.shift_to_lin - 1:
            curwin.shift_to_lin = lin - curwin.number_of_lin + 1

    def minibar(self, str txt=':'):
        #self.save_cursor()
        self.bottom()
        self.clear_line()
        if txt.endswith('\n'):
            stdout.write('\x1b[0m\r' + txt[:-1])
        else:
            stdout.write('\x1b[0m\r' + txt)
        #self.restore_cursor()

    @staticmethod
    def insert(str text):
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
