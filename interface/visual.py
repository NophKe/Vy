from vy.keys import _escape
from vy.interface.helpers import one_inside_dict_starts_with
from collections import ChainMap
from vy.global_config import DEBUG
from vy.editor import _Editor

def init(editor):
    global dictionary, minibar, _get_char
    
    dictionary = ChainMap(editor.actions.motion, editor.actions.visual)
    minibar = editor.screen.minibar

    def _get_char(REG, COUNT, key):
        """Updates mini-bar before reading a new key-strike"""
        texte = ''
        texte += (' Register: ' + REG + ' ') if REG else ''
        texte += (' Count: ' + str(COUNT) + ' ') if COUNT and COUNT != 1 else ''
        texte += (' (not fully evaluated: ' + _escape(key) + ' )') if key else ''
        lines = [texte] if texte else ['']
        
        if any(lines):
            editor.screen.minibar(*lines)
        return editor.read_stdin()
    
def loop(editor: _Editor):
    get_char = lambda: _get_char(REG, COUNT, key)
    cur_buf = editor.current_buffer
    if not cur_buf.selected_lines:
        cur_buf.start_selection()
    rv = key = REG = COUNT = ''
    key = get_char()

    if key == '"':
        REG = get_char()
        if REG not in editor.registr.valid_registers:
            minibar(f' ( Invalid register: {_escape(REG)} )')
            return
        key = get_char()
    REG = REG or '+'

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
        editor.screen.minibar(f'unrecognized key: {_escape(key)}')
        return
        
    func = dictionary[key]
    
    if func.motion:
        cancel = minibar(f' ( Processing Motion: {str(COUNT) + " times " if COUNT != 1 else ""}{_escape(key)} )')
        func(editor, count=COUNT)
        cancel()
        
    elif func.atomic:
        cancel = minibar(f' ( Processing Command: {_escape(key)} )')
        rv = func(editor)
        cancel()
        return rv
        
    elif func.stand_alone:
        cancel = minibar(f' ( Processing Command: {_escape(key)}{" on " + str(COUNT) + " lines " if COUNT != 1 else ""} )')
        selection = cur_buf.selected_lines
        cur_buf.cursor_lin_col = selection.start, 0
        rv = func(editor, count=len(selection))
        cur_buf.cursor_lin_col = selection.start, 0
        cancel()
        return rv
        
    elif func.full:
        rv = func(editor, 
                  reg=REG,
                  part=editor.current_buffer.selected_offsets) 
        return rv or 'normal'
    else:
        editor.warning(f'unrecognized key: {_escape(key)}... no (.motion .full  .atomic .stand_alon) !!!')
