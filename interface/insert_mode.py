from .. import keys as k
from ..actions import *
from ..console import get_a_key, setraw
from .helpers import one_inside_dict_starts_with, do


def GO(where):
    def func(ed, cmd):
        ed.current_buffer.move_cursor(where)
        return 'insert'
    return func

def loop(self):
    pending = list()
    self.screen.show(True)
    self.screen.minibar('-- INSERT --')
    self.screen.restore_cursor()
    while True:
        user_input  = get_a_key()
        if user_input == '\r':
            pending.append('\n')
            break
        elif user_input.isspace():
            pending.append(user_input)
            break
        elif user_input.isprintable():
            pending.append(user_input)
            self.screen.insert(user_input)
        else:
            while one_inside_dict_starts_with(dictionary, user_input):
                if user_input in dictionary:
                    break
                else:
                    user_input += get_a_key()
            self.current_buffer.insert(''.join(pending))
            if user_input in dictionary:
                return dictionary[user_input](self, None)

    self.current_buffer.insert(''.join(pending))
    return 'insert'


dictionary = {}

# Add DEL here
dictionary.update({ key: do(DO_suppr) for key in ['\x1b[3~'] })

# Add BSP here
dictionary.update({ key: do(DO_backspace) for key in ['\x08', '\x07'] })

dictionary.update( {
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
    k.C_C*7 : lambda ed, cmd: ed.warning('^C pressed seven times'),
    })
