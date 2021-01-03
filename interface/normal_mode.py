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


def show_forever(pipe):
    import time
    while True:
        start = time.time()
        if pipe.poll():
            screen = pipe.recv()
            if pipe.poll():
                continue
            screen.show()
        if (delay := time.time() - start) < 0.1:
            time.sleep(0.1)



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
    def render_screen():
        def show_screen(i_screen, i_renew, i_child_conn):
            i_screen.show(i_renew, i_child_conn )
            i_screen.infobar()
            i_screen.minibar(' -- NORMAL -- ')
        return Process(target=show_screen,
                        args=(self.screen,renew, child_conn))

    def get_char():
        self.screen.minibar(f' -- NORMAL -- {REG=} {COUNT=} {CMD=} {RANGE=} {MOTION_COUNT=}')
        return get_a_key()

    with stdin_no_echo():
        parent_conn, child_conn = Pipe()
        renew = True
        show = render_screen()
        show.start()
        timeout = 1

        while True:
            self.screen.recenter()
            if parent_conn.poll():
                while parent_conn.poll():
                    self.screen._old_screen = parent_conn.recv()
                show = render_screen()
                show.start()
            else:
                self.screen.infobar(f'(screen not fully rendered) {timeout=}')
                if parent_conn.poll(timeout / 20):
                    continue
                else:
                    timeout += 1
                    
            # those values are magic...
            REG = COUNT = CMD = RANGE = MOTION_COUNT = ''
            
            key = get_char()
            
            if key == '"':
                REG = get_char()
                if REG not in valid_registers: continue
                key = get_char()
            
            if key.isdigit():
                COUNT += key
                while (key := get_char()).isdigit(): COUNT += key
            COUNT = int(COUNT) if COUNT else 1

            while one_inside_dict_starts_with(dictionary, key):
                if key in dictionary: break
                else: key += get_char()
            else: continue

            if key in sa_cmd: 
                rv = resolver(sa_cmd, key)(self, None)
                if rv and rv != 'normal':
                    return rv
                continue

            elif key in full_cmd:
                CMD = key
                key = get_char()

                if key.isdigit():
                    MOTION_COUNT += key
                    while (key := get_char()).isdigit(): MOTION_COUNT += key
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
                    
                    return 'normal'


                while one_inside_dict_starts_with(motion_cmd, key):
                    if key in dictionary: break
                    else: key += get_char()
                else: continue

                if key not in motion_cmd: continue
                
                func = resolver(motion_cmd,key)
                RANGE = func(self.current_buffer)
                
                if isinstance(RANGE, slice):
                    old_pos, new_pos = RANGE.start, RANGE.stop
                else:
                    old_pos = self.current_buffer.tell()
                    for _ in range(COUNT * MOTION_COUNT):
                        self.current_buffer.seek(func(self.current_buffer))
                    new_pos = self.current_buffer.tell()
                
                if old_pos > new_pos:
                    old_pos, new_pos = new_pos, old_pos
                RANGE = slice(old_pos, new_pos)

                resolver(full_cmd, CMD)(self, RANGE)
                return 'normal'

            elif key in motion_cmd:
                func = resolver(motion_cmd, key)
                if not isinstance(func(self.current_buffer), slice):
                    for _ in range(COUNT):
                        self.current_buffer.seek(func(self.current_buffer))
                    continue

