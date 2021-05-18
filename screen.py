"""This module is a mess that handles screen rendering"""
from os import get_terminal_size
from sys import stdout
from itertools import chain, repeat

class Window():
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

    def __init__(self, parent, shift_to_col, shift_to_lin, buff):
        self.parent = parent
        self.shift_to_col = shift_to_col
        self.shift_to_lin = shift_to_lin
        self.buff = buff
        self._v_split_flag = False
        self.v_split_shift = 0
        self._focused = self 

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
            generator = self.buff.gen_window( self.number_of_col, 
                                                self.shift_to_lin, 
                                                self.number_of_lin + self.shift_to_lin)
            default = repeat( '~'+(' '*(self.number_of_col-1)))
            max_index = self.number_of_lin + self.shift_to_lin

            renderer =  chain(generator,default)

            for _ in range(self.number_of_lin):
                yield next(renderer)

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
        self._old_screen = list(' ' * 100)
 
    def vsplit(self):
        if self.focused != self:
            self.focused.vsplit()
        else:
            super().vsplit().set_focus()
                

    def show(self, renew=False, pipe=None):
        #self.top_left()
        self.infobar('__screen is rendering__')
        self.recenter()
        for index, line in enumerate(self.gen_window(), start=1):
            if self._old_screen[index] != line or renew:
                self.go_line(index)
                #self.clear_line()
                stdout.write(line)
                self._old_screen[index] = line
        self.bottom()
        stdout.flush()
        self.infobar()
        if pipe:
            pipe.send(self._old_screen)
            #queue.close()


    def recenter(self):
        curwin = self.focused
        lin, col = curwin.buff.cursor_lin_col
        if lin < curwin.shift_to_lin + 1:
            curwin.shift_to_lin = lin - 1
        elif lin >= curwin.number_of_lin + curwin.shift_to_lin - 1:
            curwin.shift_to_lin = lin - curwin.number_of_lin + 1

    def minibar(self, txt=':'):
        #self.save_cursor()
        self.bottom()
        self.clear_line()
        if txt.endswith('\n'):
            stdout.write('\x1b[0m\r' + txt[:-1] + '\r' )
        else:
            stdout.write('\x1b[0m\r' + txt + '\r')
        #self.restore_cursor()

    def infobar(self, txt=''):
        assert '\n' not in txt
        if not txt:
            txt = '_' * self.number_of_col
        else:
            txt = txt.center(self.number_of_col, '\u2026')

        self.go_line(self.number_of_lin + 1)
        if txt.endswith('\n'):
            stdout.write('\x1b[0m\r' + txt[:-1])
        else:
            stdout.write('\x1b[0m\r' + txt)
        #self.restore_cursor()
        self.bottom()

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
