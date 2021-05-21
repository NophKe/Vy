from time import time
from multiprocessing import Process, Pipe
from collections import ChainMap

from .helpers import one_inside_dict_starts_with, resolver, do
from ..console import get_a_key, stdin_no_echo

def loop(self):
    curbuf = self.current_buffer
    curbuf_hash = hash(curbuf)

    sa_cmd = curbuf.stand_alone_commands
    full_cmd = curbuf.full_commands
    motion_cmd = curbuf.motion_commands
    dictionary =  ChainMap(sa_cmd, full_cmd, motion_cmd)
    valid_registers = ( 'abcdefghijklmnopqrstuvwxyz'
                      + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                      + '+-*/.:%#"' )

    def render_screen():
        def show_screen(i_screen, i_renew, i_child_conn):
            i_screen.show(i_renew, i_child_conn )
            i_screen.minibar(' -- NORMAL -- ')
        return Process(target=show_screen,
                         args=(self.screen,renew, child_conn))
    def get_char():
        """ this function when used as follows REG = get_char()
            will prevent the minibar to be printed because one 
            element of fstring is waiting to be assigned (here REG)
            so the print will only happen once stdin has been read.
        """
        self.screen.minibar(f' -- NORMAL -- {REG=} {COUNT=} {CMD=} {RANGE=} {MOTION_COUNT=}')
        return self.read_stdin() #get_a_key()

    with stdin_no_echo():
        parent_conn, child_conn = Pipe()
        renew = True
        stamp = time()
        self.screen.show(True)

        while True:
            if curbuf_hash != hash(self.current_buffer):
                return
#           assert self.current_buffer is not None
            self.screen.recenter()
            if renew:
                show = render_screen()
                show.start()
                renew = False
            elif parent_conn.poll(0.2):
                self.screen.infobar()
                self.screen._old_screen = parent_conn.recv()
                show = render_screen()
                show.start()
            else:
                if time() - stamp > 10:
                    self.screen.infobar(f'__screen speed being optimized__')
                    show.kill()
                    stamp = time()
                    renew = True
                    self.screen.show(True)
                    continue
                else:
                    self.screen.infobar(f'__screen is slow to render__')
                    first = True

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
                self.screen.infobar(f'__processing command( {repr(key)} )__')
                rv = resolver(sa_cmd, key)(self, REG)
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

                if key == CMD or (len(CMD) > 1 and CMD.startswith('g') and key == 'g'):
                    self.screen.infobar(f'__processing command( {key} )__')
                    COMMAND = resolver(full_cmd, CMD)
                    flag = False
                    if not REG:
                        flag = True
                        temp = self.register["z"]
                        REG = "z" # temporary hack
                    if REG.islower():
                        self.register[REG] = ""
                        REG = REG.upper()

                    self.current_buffer.stop_undo_record()
                    self.current_buffer.set_undo_point()
                    for _ in range(MOTION_COUNT * COUNT):
                        RANGE = resolver(motion_cmd, '.')(self.current_buffer)
                        COMMAND(self, RANGE, REG)
                    self.current_buffer.start_undo_record()
                    self.register['"'] = self.register[REG.lower()]
                    if flag:
                        self.register['z'] = temp

                    return 'normal'

                while one_inside_dict_starts_with(motion_cmd, key):
                    if key in dictionary: break
                    else: key += get_char()
                else: continue

                if key not in motion_cmd: continue
                
                self.screen.infobar(f'__processing command( {key} )__')
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

                rv = resolver(full_cmd, CMD)(self, RANGE, REG)
                if rv and rv != 'normal':
                    return rv
                continue

            elif key in motion_cmd:
                self.screen.infobar(f'processing command( {key} )')
                func = resolver(motion_cmd, key)
                if not isinstance(func(self.current_buffer), slice):
                    for _ in range(COUNT):
                        self.current_buffer.seek(func(self.current_buffer))
                    continue
