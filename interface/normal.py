from vy.interface.helpers import one_inside_dict_starts_with
from vy.keys import _escape

def init(editor):
    global minibar
    minibar = editor.screen.minibar


def loop(editor, capture=True):
    """ Normal mode event-loop function """

    dictionary = dict()
    last_buffer = curbuf = motion_cmd = local_actions = None
    valid_registers     = ( 'abcdefghijklmnopqrstuvwxyz'
                            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                            '+-*/.:%#"=!0123456789')

    def update_globals():
        """if the current buffer has changed, update the action dictionnary"""
        nonlocal curbuf, dictionary, motion_cmd, local_actions, last_buffer

        if last_buffer is not (curbuf := editor.current_buffer):
            last_buffer = curbuf
            motion_cmd = curbuf.motion_commands
            local_actions = curbuf.actions 
            dictionary.clear()
            #dictionary.update(motion_cmd)
            dictionary.update(editor.actions.normal)
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
        if texte:
            minibar(texte)
        return editor.read_stdin()

    stop = not capture
    capture = True

    while True and capture:
        if stop:
            capture = False

        update_globals()
        key = REG = CMD = RANGE = MOTION_COUNT = ''
        COUNT = ''
        key = get_char()

        if key == '"':
            REG = get_char()
            if REG not in valid_registers:
                minibar(f' ( Invalid register: {_escape(REG)} )')
                continue
            key = get_char()

        if key in '123456789': # No zero here
            while key in '0123456789':
                COUNT += key
                key = get_char()
        COUNT = int(COUNT) if COUNT else 1

        while one_inside_dict_starts_with(dictionary, key):
            if key in dictionary:
                break
            key += get_char()
        else:
            minibar(f' ( Invalid command: {_escape(key)} )')
            continue

        if key in local_actions:
            return local_actions[key](editor)

        action = dictionary[key]
        
        if action.motion:
            minibar(f' ( Processing Motion: {str(COUNT) + " times " if COUNT != 1 else ""}{_escape(key)} )')
            rv = action(editor, count=COUNT)
            minibar('')
            if rv and rv != 'normal':
                return rv
            continue

        if action.atomic:
            cancel_minibar = minibar(f' ( Processing Command: {_escape(key)} )')
            rv = action(editor, count=COUNT)
            cancel_minibar()
            if rv and rv != 'normal':
                return rv
            continue

        elif action.stand_alone:
            cancel_minibar = minibar(f' ( Processing Command: {_escape(key)} {COUNT} times)')
            rv = action(editor, reg=REG if REG else '"', count=COUNT)
            cancel_minibar()
            if rv and rv != 'normal':
                return rv
            continue

        elif action.full:
            CMD = key
            key = get_char()

            while key in '0123456789':
                MOTION_COUNT += key
                key = get_char()
            MOTION_COUNT = int(MOTION_COUNT) if MOTION_COUNT else 1

            if key == CMD or (len(CMD) > 1 and CMD.startswith('g') and key == 'g'):
                COUNT = COUNT * MOTION_COUNT
                minibar(f'( Processing Command: {COUNT} {_escape(CMD)} )')
                RANGE = curbuf._get_range(f'#.:#+{COUNT}')
                rv = action(editor, reg=REG if REG else '"', part=RANGE)
                minibar('')
                if rv and rv != 'normal':
                    return rv
                continue

            while one_inside_dict_starts_with(motion_cmd, key):
                if key in motion_cmd: break
                else: key += get_char()
            else:
                minibar(f'Invalid motion: {_escape(key)}')
                continue
            func = motion_cmd[key]
            RRANGE = func()
            COUNT = COUNT * MOTION_COUNT

            minibar(f'( Processing Command: {_escape(CMD)}{COUNT}{_escape(key)} )')

            if isinstance(RRANGE, slice): # correct! discard COUNT in case of slice
                old_pos, new_pos = RRANGE.start, RRANGE.stop
            else:
                old_pos = curbuf.cursor
                for _ in range(COUNT):
                    curbuf.cursor = func()
                new_pos = curbuf.cursor

            RRANGE = slice(min(old_pos, new_pos), max(old_pos, new_pos))

            rv = action(editor, reg=REG if REG else '"', part=RRANGE)
            minibar('')
            if rv and rv != 'normal':
                return rv
            continue
