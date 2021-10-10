from multiprocessing import Process

from .. import keys as k
from ..actions import *
from ..console import get_a_key, stdin_no_echo
from .helpers import one_inside_dict_starts_with, do


def GO(where):
    def func(ed, cmd):
        ed.current_buffer.move_cursor(where)
        return 'insert'
    return func

def loop(self):
    curbuf = self.current_buffer
    screen = self.screen
    show = None
    
    with stdin_no_echo():
        while True:
            if show is None: # First loop
                curbuf.stop_undo_record()
                screen.show(True)

            show = Process(target=screen.show, args=(True,))
            show.start()
            screen.minibar(' -- INSERT --')
            
            user_input  = self.read_stdin()
#            show.kill()

            if user_input in '²\x1b':
                curbuf.set_undo_point()
                curbuf.start_undo_record()
                show.kill()
                return 'normal'

            if user_input == '\r':
                curbuf.insert('\n')
                curbuf.set_undo_point()
                show.kill()
                continue

            if user_input == ' ':
                curbuf.insert(' ')
                curbuf.set_undo_point()
                show.kill()
                continue
            
            if user_input.isprintable():
                curbuf.insert(user_input)
                show.kill()
                continue

            while one_inside_dict_starts_with(dictionary, user_input):
                if user_input in dictionary:
                    curbuf.start_undo_record()
                    rv = dictionary[user_input](self, None)
                    show.kill()
                    if rv and rv != 'insert':
                        return rv
                    curbuf.stop_undo_record()
                    break
                else:
                    user_input += self.read_stdin()

dictionary = {
# Deletion
    k.backspace : DO_backspace,
    k.suppr : DO_suppr,
# Page up/down
    k.page_up   : DO_page_up,
    k.page_down : DO_page_down,
# Control + Arrow
    k.C_right   : GO('w'),
    k.C_left    : GO('b'),

# Shift + Arrow
    k.S_right   : GO('w'),
    k.S_left    : GO('b'),

# Arrows
    k.left  : GO('h'),
    k.down  : GO('j'),
    k.up    : GO('k'),
    k.right : GO('l'),

# leave insert mode
    '\x1b'  : do(mode='normal') ,
    '²'     : do(mode='normal') ,
    # thos two are also encoded in function loop...
    # dunno if its worth or not 
    k.C_C*7 : lambda ed, cmd: ed.warning('^C pressed seven times'),

# inserter
    '\t'    : DO_insert_expandtabs,
    }
