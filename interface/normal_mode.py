from multiprocessing import Process, Pipe
from collections import ChainMap

from .helpers import one_inside_dict_starts_with, resolver, do

from ..console import get_a_key, stdin_no_echo
from ..actions import *
from .. import keys as k
from ..textfile.motions import motion

GO = lambda where: lambda ed, cmd: ed.current_buffer.move_cursor(where)

def DELETE(ed, part):
    curbuf = ed.current_buffer
    ed.register['"'] = curbuf[part]
    return curbuf.__delitem__(part)

def SWAP_CASE(ed, part):
    new_txt = ed.current_buffer[part].swapcase()
    ed.current_buffer[part] = new_txt
    ed.current_buffer.cursor += len(new_txt)



full_cmd = {'d' : DELETE,
            'g~'    : SWAP_CASE,
}

sa_cmd = {
    'p' : DO_paste,
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
    '?'     : lambda x, arg: x.warning(f'{x.current_buffer.cursor_lin_col = }'),
    'n' : DO_normal_n,

# recenter
    'zz'    : DO_zz,
    'zt'    : DO_zt,
    'zb'    : DO_zb,

# edition
    k.suppr : 'x',
    'x' : DO_suppr,
    'X' : lambda ed, cmd: ed.current_buffer.backspace(),
    '~' : DO_normal_tilde, 

# sub-modes
    'r' : DO_r,
    '/' : DO_find,

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

    with stdin_no_echo():
        parent_conn, child_conn = Pipe()
        renew = True
        show = Process(target=self.screen.show, args=(renew, child_conn))
        show.start()

        while True:
            self.screen.minibar(' -- NORMAL -- ')
            self.screen.recenter()
            while parent_conn.poll():
                self.screen._old_screen = parent_conn.recv()
            else:
                show.kill()
                show = Process(target=self.screen.show, args=(renew, child_conn))
                show.start()


            REG = COUNT = CMD = RANGE = MOTION_COUNT = ''

            key = get_a_key()
            
            if key == '"':
                REG = get_a_key()
                if REG not in valid_registers: continue
                key = get_a_key()
            
            if key.isdigit():
                COUNT += key
                while (key := get_a_key()).isdigit(): COUNT += key
            COUNT = int(COUNT) if COUNT else 1

            while one_inside_dict_starts_with(dictionary, key):
                if key in dictionary: break
                else: key += get_a_key()
            else: continue

            if key in sa_cmd: return resolver(sa_cmd, key)(self, None)

            elif key in full_cmd:
                CMD = key
                key = get_a_key()

                if key.isdigit():
                    MOTION_COUNT += key
                    while (key := get_a_key()).isdigit(): MOTION_COUNT += key
                MOTION_COUNT = int(MOTION_COUNT) if MOTION_COUNT else 1

                if key == CMD or (len(CMD) > 1 
                                    and CMD.startswith('g')
                                    and key == 'g'):
                    COMMAND = resolver(full_cmd, CMD)


                    self.current_buffer.stop_undo_record()
                    self.current_buffer.set_undo_point()
                    for _ in range(MOTION_COUNT * COUNT):
                        MOTION = resolver(motion_cmd, '.')(self.current_buffer)
                        COMMAND(self, MOTION)
                    self.current_buffer.start_undo_record()
                    
                    #show.join(1)
                    #show.kill()
                    return 'normal'


                while one_inside_dict_starts_with(motion_cmd, key):
                    if key in dictionary: break
                    else: key += get_a_key()
                else: continue

                if key not in motion_cmd: continue
                
                if key.startswith('i'):
                    func = resolver(motion_cmd,key)
                    self.current_buffer.seek(func(self.current_buffer))
                    func = resolver(motion_cmd,key[1:])
                else:
                    func = resolver(motion_cmd,key)

                old_pos = self.current_buffer.tell()
                for _ in range(COUNT * MOTION_COUNT):
                    self.current_buffer.seek(func(self.current_buffer))
                new_pos = self.current_buffer.tell()

                if old_pos < new_pos:
                    RANGE = slice(old_pos, new_pos)
                    self.current_buffer.seek(old_pos)
                else:
                    RANGE = slice(new_pos, old_pos)
                    self.current_buffer.seek(new_pos)

                resolver(full_cmd, CMD)(self, RANGE)
                return 'normal'

            elif key in motion_cmd:
                func = resolver(motion_cmd, key)
                #show.join(1)
                for _ in range(COUNT):
                    self.current_buffer.seek(func(self.current_buffer))
                #show.kill()
                continue

