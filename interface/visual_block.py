
from vy.keys import _escape
from vy.interface.helpers import one_inside_dict_starts_with
from collections import ChainMap

def init(editor):
    global dictionary
    dictionary = ChainMap(editor.actions.motion,
                            editor.actions.visual)

    def get_char():
        """Updates mini-bar before reading a new key-strike"""
        texte = ''
        texte += (' Register: ' + REG + ' ') if REG else ''
        texte += (' Count: ' + str(COUNT) + ' ') if COUNT and COUNT != 1 else ''
        texte += (' (not fully evaluated: ' + _escape(key) + ' )') if key else ''
        lines = [texte] if texte else []
        
        selected_off = 'Selected offsets : {editor.current_buffer.selected_offsets}'        
        selected_lin = 'Selected lines   : {editor.current_buffer.selected_lines}'        
        lines.append(selected_off)
        lines.append(selected_lin)
        
        editor.screen.minibar(*lines)
        return editor.read_stdin()

def loop(editor):
    def get_char():
        """Updates mini-bar before reading a new key-strike"""
        texte = ''
        texte += (' Register: ' + REG + ' ') if REG else ''
        texte += (' Count: ' + str(COUNT) + ' ') if COUNT and COUNT != 1 else ''
        texte += (' (not fully evaluated: ' + _escape(key) + ' )') if key else ''
        lines = [texte] if texte else []
        
        lines.append(f'Selected offsets : {editor.current_buffer.selected_offsets}')
        lines.append(f'Selected lines   : {editor.current_buffer.selected_lines}')       
        
        editor.screen.minibar(*lines)
        return editor.read_stdin()
        
    valid_registers     = ( 'abcdefghijklmnopqrstuvwxyz'
                            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                            '+-*/.:%#"=!0123456789')
                            
    cur_buf = editor.current_buffer
    cur_buf.start_selection()
    try:
        while True:
            key = REG = COUNT = ''
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
                editor.screen.minibar(f'unrecognized key: {_escape(key)}')
                continue
                
            func = dictionary[key]
            
            if func.motion:
                func(editor, count=COUNT)
                continue
            elif func.atomic:
                return func(editor)
            elif func.stand_alone:
                selection = cur_buf.selected_lines
                cur_buf.cursor_lin_col = selection.start, 0
                rv = func(editor, count=len(selection))
                cur_buf.cursor_lin_col = selection.start, 0
                return rv or 'normal'
            elif func.full:
                return func(editor, part=editor.current_buffer.selected_offsets) or 'normal'
            else:
                editor.screen.minibar(f'unrecognized key: {_escape(key)}')
                editor.current_buffer.stop_selection()
                return 'normal'
        return 'normal'
    finally:
        editor.current_buffer.stop_selection()
