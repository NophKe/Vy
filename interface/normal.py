from vy.interface.helpers import one_inside_dict_starts_with
from vy.keys import _escape

dictionary = dict()
curbuf_hash = curbuf = motion_cmd = local_actions = None
valid_registers     = ( 'abcdefghijklmnopqrstuvwxyz'
                        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                        '+-*/.:%#"=' )

def loop(editor):
    """ Normal mode event-loop function """

    def update_globals():
        """if the current buffer has changed, update the action dictionnary"""
        global curbuf_hash, curbuf, dictionary, motion_cmd, local_actions
        if not curbuf or curbuf_hash != curbuf:
            curbuf = editor.current_buffer
            motion_cmd = curbuf.motion_commands
            local_actions = curbuf.actions 

            dictionary.update(editor.actions.normal)
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
        if texte:
            editor.screen.minibar(texte)
        return editor.read_stdin()

    while True:
        update_globals()
        key = REG = CMD = RANGE = MOTION_COUNT = ''
        COUNT = ''
        key = get_char()

        if key == '"':
            REG = get_char()
            if REG not in valid_registers:
                editor.screen.minibar(f' ( Invalid register: {_escape(REG)} )')
                continue
            key = get_char()

        while key in '0123456789':
            COUNT += key
            key = get_char()
        COUNT = int(COUNT) if COUNT else 1

        while one_inside_dict_starts_with(dictionary, key):
            if key in dictionary:
                break
            else:
                key += get_char()
        else:
            editor.screen.minibar(f' ( Invalid command: {_escape(key)} )')
            continue

        if key in local_actions:
            return local_actions[key](editor)

        if key in motion_cmd:
            editor.screen.minibar(f' ( Processing Command {_escape(key)} )')
            for _ in range(COUNT):
                curbuf.move_cursor(key)
            editor.screen.minibar('')
            continue
        
        #editor.current_buffer.set_undo_point()
        action = dictionary[key]

        if action.atomic:
            editor.screen.minibar(f' ( Processing Command {_escape(key)} )')
            rv = action(editor)
            editor.screen.minibar('')
            if rv and rv != 'normal':
                return rv
            continue

        elif action.stand_alone:
            editor.screen.minibar(f' ( Processing Command: {_escape(key)} )')
            rv = action(editor, reg=REG if REG else '"', count=COUNT)
            editor.screen.minibar('')
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
                editor.screen.minibar(f'( Processing Command: {_escape(CMD)} on {COUNT} lines )')
                RANGE = curbuf._get_range(f'#.:#+{COUNT}')
                rv = action(editor, reg=REG if REG else '"', part=RANGE)
                editor.screen.minibar('')
                if rv and rv != 'normal':
                    return rv
                continue

            while one_inside_dict_starts_with(motion_cmd, key):
                if key in motion_cmd: break
                else: key += get_char()
            else:
                editor.screen.minibar(f'Invalid motion: {_escape(key)}')
                continue
            func = motion_cmd[key]
            RRANGE = func()
            COUNT = COUNT * MOTION_COUNT

            editor.screen.minibar(f'( Processing Command: {_escape(CMD)}{COUNT}{_escape(key)} )')

            if isinstance(RRANGE, slice): # correct! discard COUNT in case of slice
                old_pos, new_pos = RRANGE.start, RRANGE.stop
            else:
                old_pos = curbuf.cursor
                for _ in range(COUNT):
                    curbuf.cursor = func()
                new_pos = curbuf.cursor

            RRANGE = slice(min(old_pos, new_pos), max(old_pos, new_pos))

            rv = action(editor, reg=REG if REG else '"', part=RRANGE)
            editor.screen.minibar('')
            if rv and rv != 'normal':
                return rv
            continue
