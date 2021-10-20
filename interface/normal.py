from collections import ChainMap

from .helpers import one_inside_dict_starts_with, resolver, do
from ..console import get_a_key, stdin_no_echo

def loop(self):
    curbuf = self.current_buffer

    sa_cmd = curbuf.stand_alone_commands
    full_cmd = curbuf.full_commands
    motion_cmd = curbuf.motion_commands
    dictionary =  ChainMap(sa_cmd, full_cmd, motion_cmd)

    valid_registers = ( 'abcdefghijklmnopqrstuvwxyz'
                      + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                      + '+-*/.:%#"' )
    def get_char():
        self.screen.minibar(f' -- NORMAL -- REG={REG} {COUNT=} {CMD=} {RANGE=} {MOTION_COUNT=}')
        return self.read_stdin() #get_a_key()

    with stdin_no_echo():
        while True:
            self.screen.show(True)
            REG = '"'
            COUNT = CMD = RANGE = MOTION_COUNT = ''

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
                #show.kill()
                self.screen.infobar(f'processing command( {repr(key)} )')
                rv = resolver(sa_cmd, key)(self, REG)
                return rv

            elif key in motion_cmd:
                #show.kill()
                self.screen.infobar(f'processing command( {repr(key)} )')
                func = resolver(motion_cmd, key)
                target = func(curbuf)
                if isinstance(target, slice):
                    continue
                curbuf.cursor = target
                for _ in range(COUNT - 1):
                    curbuf.cursor = (func(curbuf))
                continue

            elif key in full_cmd:
                CMD = key
                key = get_char()

                if key.isdigit():
                    MOTION_COUNT += key
                    while (key := get_char()).isdigit(): MOTION_COUNT += key
                MOTION_COUNT = int(MOTION_COUNT) if MOTION_COUNT else 1

                if key == CMD or (len(CMD) > 1 and CMD.startswith('g') and key == 'g'):
                    self.screen.infobar(f'processing command( {key} )')
                    COUNT = COUNT * MOTION_COUNT
                    COMMAND = resolver(full_cmd, CMD)
                    RANGE = curbuf._get_range(f'#.:#+{COUNT}')
                    return COMMAND(self, RANGE, REG)

                while one_inside_dict_starts_with(motion_cmd, key):
                    if key in motion_cmd: 
                        break
                    else: 
                        key += get_char()
                else: 
                    return 'normal'

                self.screen.infobar(f'processing command( {key} )')
                func = resolver(motion_cmd,key)
                RANGE = func(curbuf)
                
                if isinstance(RANGE, slice):
                    old_pos, new_pos = RANGE.start, RANGE.stop
                else:
                    old_pos = curbuf.tell()
                    for _ in range(COUNT * MOTION_COUNT):
                        curbuf.seek(func(curbuf))
                    new_pos = curbuf.tell()
                
                if old_pos > new_pos:
                    old_pos, new_pos = new_pos, old_pos
                RANGE = slice(old_pos, new_pos)

                return resolver(full_cmd, CMD)(self, RANGE, REG)

