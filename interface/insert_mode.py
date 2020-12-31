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
            if not show:
                screen.show(True)
                screen.minibar(' -- INSERT --')
                show = Process(target=screen.show, args=())
                show.start()
            else:
                show.join(0.5)
                show = Process(target=screen.show, args=(True,))
                show.start()
            
            user_input  = get_a_key()
            show.kill()

            if user_input == '\r':
                curbuf.insert('\n')
                #show = None
            elif user_input.isprintable():
                curbuf.insert(user_input)
                #show.kill()
            else:
                while one_inside_dict_starts_with(dictionary, user_input):
                    if user_input in dictionary:
                        rv = dictionary[user_input](self, None)
                        if rv and rv != 'insert':
                            return rv
                        #show = None
                        break
                    else:
                        user_input += get_a_key()




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

# inserter
    '\t'    : DO_insert_expandtabs,
    })
