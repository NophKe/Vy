from multiprocessing import Process
from threading import Thread
from vy.interface.helpers import one_inside_dict_starts_with
from vy.console import stdin_no_echo
from vy.keys import _escape

dictionary = dict()
curbuf_hash = curbuf = motion_cmd = local_actions = None
valid_registers     = ( 'abcdefghijklmnopqrstuvwxyz'
                        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                        '+-*/.:%#"=' )

def loop(self):
    """ Normal mode event-loop function """

    def update_globals():
        """if the current buffer has changed, update the action dictionnary"""
        global curbuf_hash, curbuf, dictionary, motion_cmd, local_actions
        if not curbuf or curbuf_hash != curbuf:
            curbuf = self.current_buffer
            motion_cmd = curbuf.motion_commands
            local_actions = curbuf.actions 

            dictionary.update(self.actions.normal)
            dictionary.update(motion_cmd)
            dictionary.update(local_actions)

    def get_char():
        """Updates mini-bar before reading a new key-strike"""
        texte                   = ''
        if REG                  : texte += ' Register: ' + REG + ' '
        if COUNT and COUNT != 1 : texte += ' Count: ' + str(COUNT) + ' '
        if CMD                  : texte += ' Command: ' + CMD + ' '
        if MOTION_COUNT         : texte += ' Motion count: ' + str(MOTION_COUNT) + ' '
        if RANGE                : texte += ' Motion: ' + RANGE + ' '
        if key                  : texte += ' (not fully evaluated: ' + _escape(key) + ' )'
        if texte: self.screen.minibar(texte)
        return self.read_stdin()

    def screen():
        while True:
            Editor.show_screen()
        if screen is None:
            screen = Thread(target=self.show)

    show = lambda : None
    show.join = show
    with stdin_no_echo():
        while True:
            update_globals()
            new_show = Thread(target=self.show_screen, args=(True,), daemon=True)
            show.join()
            new_show.start()
            show = new_show

            key = REG = CMD = RANGE = MOTION_COUNT = ''
            COUNT = ''
            #self.show_screen(True)
            key = get_char()

            if key == '"':
                REG = get_char()
                if REG not in valid_registers:
                    self.screen.minibar(f'Invalid register: {_escape(REG)}')
                    continue
                key = get_char()

            if key.isdigit():
                COUNT += key
                while (key := get_char()) in '0123456789':
                    COUNT += key
            COUNT = int(COUNT) if COUNT else 1

            while one_inside_dict_starts_with(dictionary, key):
                if key in dictionary:
                    break
                else:
                    key += get_char()
            else:
                self.screen.minibar(f'Invalid command: {_escape(key)}')
                continue

            action = dictionary[key]
            
            if key in local_actions:
                return action(self)

            if key in motion_cmd:
                self.screen.infobar(f'processing command( {_escape(key)} )')
                self.screen.minibar(f'')
                for _ in range(COUNT):
                    curbuf.move_cursor(key)
                continue

            if action.atomic:
                self.screen.infobar(f'processing command( {repr(key)} )')
                self.screen.minibar(f'')
                rv = action()
                if rv and rv != 'normal':
                    return rv
                continue

            elif action.stand_alone:
                self.screen.infobar(f'processing command( {repr(key)} )')
                self.screen.minibar(f'')
                rv = action(reg=REG if REG else '"', count=COUNT)
                if rv and rv != 'normal':
                    return rv
                continue

            elif action.full:
                CMD = key
                key = get_char()

                if key.isdigit():
                    MOTION_COUNT += key
                    while (key := get_char()).isdigit(): MOTION_COUNT += key
                MOTION_COUNT = int(MOTION_COUNT) if MOTION_COUNT else 1

                if key == CMD or (len(CMD) > 1 and CMD.startswith('g') and key == 'g'):
                    COUNT = COUNT * MOTION_COUNT
                    self.screen.infobar(f'( Processing Command: {_escape(CMD)} on {COUNT} lines )')
                    self.screen.minibar(f'')
                    RANGE = curbuf._get_range(f'#.:#+{COUNT}')
                    rv = action(reg=REG if REG else '"', part=RANGE)
                    if rv and rv != 'normal':
                        return rv
                    continue

                while one_inside_dict_starts_with(motion_cmd, key):
                    if key in motion_cmd: break
                    else: key += get_char()
                else:
                    self.screen.minibar(f'Invalid motion: {_escape(key)}')
                    continue
                func = motion_cmd[key]
                RANGE = func()
                COUNT = COUNT * MOTION_COUNT

                self.screen.infobar(f'( Processing Command: {_escape(CMD)}{COUNT}{_escape(key)} )')
                self.screen.minibar(f'')

                if isinstance(RANGE, slice): # correct! discard COUNT in case of slice
                    old_pos, new_pos = RANGE.start, RANGE.stop
                else:
                    old_pos = curbuf.cursor
                    for _ in range(COUNT):
                        curbuf.cursor = func()
                    new_pos = curbuf.cursor

                RANGE = slice(min(old_pos, new_pos), max(old_pos, new_pos))

                rv = action(reg=REG if REG else '"', part=RANGE)
                if rv and rv != 'normal':
                    return rv
                continue
