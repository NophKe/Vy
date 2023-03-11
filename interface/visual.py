from vy.keys import _escape
from vy.interface.helpers import one_inside_dict_starts_with
from collections import ChainMap

def init(editor):
    global dictionary
    dictionary = ChainMap(editor.actions.motion,
                            editor.actions.visual)

def loop(editor):
    cur_buf = editor.current_buffer
    cur_buf.start_selection()
    try:
        while True:
            key = editor.read_stdin()
            
            if key in dictionary:
                func = dictionary[key]
                if func.motion or func.atomic:
                    func(editor)
                    continue
                elif func.stand_alone:
                    selection = cur_buf.selected_lines
                    cur_buf.cursor_lin_col = selection.start, 0
                    rv = func(editor, count=len(selection))
                elif func.full:
                    rv = func(editor, part=editor.current_buffer.selected_offsets) or 'normal'
                editor.current_buffer.stop_selection()
                return rv

            elif one_inside_dict_starts_with(dictionary, key):
#                while one_inside_dict_starts_with(dictionary, key):
#                   pass                  
                continue
            else:
                editor.screen.minibar(f'unrecognized key: {_escape(key)}')
                break
        return 'normal'
    finally:
        editor.current_buffer.stop_selection()
