"""
    *********************************
    ****    The «Normal» Mode    ****
    *********************************

This is Vy's version of the normal mode loop of the classical vi-like
editors.  There is not much to know about it except that all commands
belonging to the commands categories will be handled in a similar
fashion and argument parsing algorithm is precisely defined.

Action writers are invited to read th source for more accurate description.

"""

from vy.interface.helpers import one_inside_dict_starts_with
from vy.keys import _escape
#from time import time

def _get_char(editor, REG, COUNT, CMD, MOTION_COUNT, RANGE, key):
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

def loop(editor, capture=True):
    """ Normal mode event-loop function """
    get_char = lambda: _get_char(editor, REG, COUNT, CMD, MOTION_COUNT, RANGE, key)

    dictionary = {}
    minibar = editor.screen.minibar
    curbuf = editor.current_buffer
    motion_cmd = editor.actions.motion
    local_actions = curbuf.actions 
    #dictionary.update(motion_cmd)
    dictionary.update(editor.actions.normal)
    dictionary.update(local_actions)

    key = REG = CMD = RANGE = MOTION_COUNT = ''
    COUNT = ''
    key = get_char()

    if key == '"':
        REG = get_char()
        if REG not in editor.registr.valid_registers:
            minibar(f' ( Invalid register: {_escape(REG)} )')
            return
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
        return

    if key in local_actions:
        return local_actions[key](editor)

    action = dictionary[key]
    
    if action.motion:
        cancel = minibar(f' ( Processing Motion: {str(COUNT) + " times " if COUNT != 1 else ""}{_escape(key)} )')
        rv = action(editor, count=COUNT)
        cancel()
        return rv

    if action.atomic:
        cancel_minibar = minibar(f' ( Processing Command: {_escape(key)} )')
        rv = action(editor, count=COUNT)
        cancel_minibar()
        return rv

    elif action.stand_alone:
        cancel_minibar = minibar(f' ( Processing Command: {_escape(key)} {COUNT} times)')
        rv = action(editor, reg=REG if REG else '"', count=COUNT)
        cancel_minibar()
        return rv

    elif action.full:
        CMD = key
        key = get_char()

        if key in '123456789':
            while key in '0123456789':
                MOTION_COUNT += key
                key = get_char()
        MOTION_COUNT = int(MOTION_COUNT) if MOTION_COUNT else 1

        if key == CMD:
            COUNT = COUNT * MOTION_COUNT
            cancel = minibar(f'( Processing Command: {COUNT} {_escape(CMD)} )')
            line_idx, start = curbuf.current_line_off
            
            try: stop = curbuf.lines_offsets[line_idx + COUNT]
            except IndexError: stop = len(curbuf)
            
            rv = action(editor, reg=REG if REG else '"', part=slice(start,stop))
            cancel()
            return rv

        while one_inside_dict_starts_with(motion_cmd, key):
            if key in motion_cmd: break
            else: key += get_char()
        else:
            minibar(f'Invalid motion: {_escape(key)}')
            return 
        
        COUNT = COUNT * MOTION_COUNT
        curbuf.start_selection()
        
        motion_cmd[key](editor, count=COUNT)   #new
        
        RRANGE = curbuf.selected_offsets
        curbuf.stop_selection()

        cancel = minibar(f'( Processing Command: {_escape(CMD)}{COUNT}{_escape(key)} )')

        rv = action(editor, reg=REG if REG else '"', part=RRANGE)
        cancel()
        return rv

