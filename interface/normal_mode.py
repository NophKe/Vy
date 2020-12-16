from collections import ChainMap

from .helpers import one_inside_dict_starts_with, resolver, do

from ..console import get_a_key, setnoecho
from ..actions import *
from .. import keys as k
from ..textfile.motions import motion

GO = lambda where: lambda ed, cmd: ed.current_buffer.move_cursor(where)

def DELETE(ed, part):
    return ed.current_buffer.__delitem__(part)



full_cmd = {'d': DELETE}

sa_cmd = {
# page scrolling 
    k.page_up   : DO_page_up,
    k.page_down : DO_page_down,

# goto insert_mode
    'O'   : do( GO('0'), r"x.current_buffer.insert('\n')", GO('k'), mode='insert'),
    'o'   : do( GO('$'), r"x.current_buffer.insert('\n')", mode='insert'),
    'i'   : do(mode='insert'),
    'I'   : do( GO('0'), mode='insert'),
    'a'   : do( GO('l'), mode='insert'),
    'A'   : do( GO('$'), mode='insert'),
    k.insert    : do(mode='insert'),
    'i'   : do(mode='insert'),

# other modes
    ':'     : do(mode='command'),

# leave
    'ZZ'    : do( DO_try_to_save, DO_exit_nice),
    'ZQ'    : DO_force_leave_current_window,

# misc
    k.C_R   : lambda ed, cmd: ed.current_buffer.redo(),
    'u'     : lambda ed, cmd: ed.current_buffer.undo(),
    '?'     : lambda x, arg: (x.screen.minibar(str(x.current_buffer.cursor_lin_col)), input()),

# recenter
    'zz'    : DO_zz,
    'zt'    : DO_zt,
    'zb'    : DO_zb,

# edition
    k.suppr : 'x',
    'x' : DO_suppr,
    'X' : lambda ed, cmd: ed.current_buffer.backspace(),

# sub-modes
    'r' : DO_r,

# window manipulation
    k.C_W + k.left : DO_focus_right_window,
    k.C_W + k.C_H   : DO_focus_left_window,
    k.C_W + 'h' : DO_focus_left_window,
    
    k.C_W + k.right : DO_focus_right_window,
    k.C_W + k.C_L   : DO_focus_right_window,
    k.C_W + 'l' : DO_focus_right_window,
    
    k.C_W + 'o' : DO_keep_only_current_window,
    k.C_W + k.C_O   : DO_keep_only_current_window,

    k.C_W + k.C_V   : DO_vsplit,
    k.C_W + 'v' : DO_vsplit,
    k.C_W + 'V' : DO_vsplit,
}

motion_cmd = {
# control + Arrow
    k.C_left  : 'b',
    k.C_right : 'w',
# shift + Arrow
    k.S_left  : 'b',
    k.S_right : 'w',
# arrows
    k.left  : 'h',
    k.right : 'l',
    k.up    : 'k',
    k.down  : 'j',
# other
    ' '     : 'l',
    '\r'    : 'j',
}
motion_cmd = ChainMap(motion, motion_cmd)

dictionary =  ChainMap(sa_cmd, full_cmd, motion_cmd)

valid_registers = 'abcdef'

    
def loop(self):
    def getchar():
        rv = get_a_key()
        self.screen.insert(rv)
        return rv

    while True:
        self.screen.show(True)
        self.screen.minibar('-- NORMAL -- \t\t\t')
        REG = ''
        COUNT = ''
        CMD = ''
        RANGE = ''
        MOTION_COUNT = ''

        key = getchar()

        if key == '"':
            REG = getchar()
            if REG not in valid_registers:
                continue
            key = getchar()

        if key.isdigit():
            COUNT += key
            while (key := getchar()).isdigit():
                COUNT += key
        COUNT = int(COUNT) if COUNT else 1

        while one_inside_dict_starts_with(dictionary, key):
            if key in dictionary:
                break
            else:
                key += getchar()
        else:
            continue

        if key in sa_cmd:
            return resolver(sa_cmd, key)(self, None)

        elif key in full_cmd:
            CMD = key
            key = getchar()

            if key.isdigit():
                MOTION_COUNT += key
                while (key := getchar()).isdigit():
                    MOTION_COUNT += key
            MOTION_COUNT = int(MOTION_COUNT) if MOTION_COUNT else 1

            if key == CMD:
                COMMAND = resolver(full_cmd, CMD)
                for _ in range(MOTION_COUNT * COUNT):
                    MOTION = resolver(motion_cmd, '.')(self.current_buffer)
                    COMMAND(self, MOTION)
                return 'normal'


            while one_inside_dict_starts_with(motion_cmd, key):
                if key in dictionary:
                    break
                else:
                    key += getchar()
            else:
                continue

            if key not in motion_cmd:
                continue
            
            if key.startswith('i'):
                self.current_buffer.seek(
resolver(motion_cmd,key)(self.current_buffer)
)
                func = resolver(motion_cmd,key[1:])
            else:
                func = resolver(motion_cmd,key)

            for _ in range(COUNT):
                old_pos = self.current_buffer.tell()
                for _ in range(MOTION_COUNT):
                    self.current_buffer.seek(func(self.current_buffer))
                new_pos = self.current_buffer.tell()
                if old_pos < new_pos:
                    RANGE = range(old_pos, new_pos)
                    self.current_buffer.seek(old_pos)
                else:
                    RANGE = range(new_pos, old_pos)
                    self.current_buffer.seek(new_pos)

                resolver(full_cmd, CMD)(self, RANGE)
            return 'normal'

        elif key in motion_cmd:
            func = resolver(motion_cmd, key)
            for _ in range(COUNT):
                self.current_buffer.seek(func(self.current_buffer))
            return 'normal'
