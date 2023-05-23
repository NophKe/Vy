from vy.keys import _escape

from vy.interface.helpers import one_inside_dict_starts_with
from vy import keys as k

def _no_undo_suppr(editor):
    if editor.current_buffer.string[editor.current_buffer.cursor] != '\n':
        editor.current_buffer.suppr()
        return True

def _no_undo_backspace(editor):
    if editor.current_buffer.string[editor.current_buffer.cursor-1] != '\n':
        editor.current_buffer.backspace()
        return True

def _no_undo_right(editor):
    dictionary[k.right](editor)
    return True

def _no_undo_left(editor):
    dictionary[k.left](editor)
    return True

minidict = { k.suppr: _no_undo_suppr,
             k.left : _no_undo_left,
             k.right: _no_undo_right,
             k.backspace: _no_undo_backspace,
             }


def monoline_loop(editor):
    last_insert = ''
    try:
        editor.current_buffer.set_undo_record(False)
        last_insert = ''
        while True:
            key_press = editor.visit_stdin()
            if key_press in minidict:
                if minidict[key_press](editor):
                    editor.read_stdin()
                    continue
                else:
                    break

            if key_press in editor.actions.insert:
                break
        
            editor.current_buffer.insert(key_press)
            last_insert += editor.read_stdin()

    finally:
        if last_insert:
            editor.registr['.'] = last_insert
        editor.screen.minibar(' ( New undo point. )')
        editor.current_buffer.set_undo_record(True)

def init(editor):
    global get_a_key, minibar, dictionary, minidict
    get_a_key = editor.read_stdin
    minibar = editor.screen.minibar
    dictionary = editor.actions.insert
    
def loop(editor):
    while True:
        monoline_loop(editor)
        user_input = editor.read_stdin()

        if user_input in dictionary:
            cancel_minibar = minibar(f' ( Processing command: {_escape(user_input)} )')
            rv = dictionary[user_input](editor)
            cancel_minibar()
            if rv and rv != 'insert':
                return rv
        else:
            minibar(f' ( Invalid command: {_escape(user_input)} )')

        
        #if user_input.isprintable() or user_input.isspace() or user_input in minidict:
            #curbuf.set_undo_record(True)
            #cancel_minibar = minibar(' ( New undo point. )')
            #
            #curbuf.set_undo_record(False)
            #curbuf.insert(user_input)
            #last_insert += user_input
            #while True:
                #user_input = get_a_key()
                #if user_input in minidict and minidict[user_input](editor):
                        #continue
                #if user_input.isprintable() or user_input.isspace() \
                        #and not user_input in dictionary            \
                        #and not any(k.startswith(user_input) for k in dictionary):
                    #curbuf.insert(user_input)
                    #last_insert += user_input
                    #continue
                #curbuf.set_undo_record(True)
                #cancel_minibar()
                #break
            #editor.registr['.'] = last_insert
            #last_insert = ''
            #continue
#
#
        #elif one_inside_dict_starts_with(dictionary, user_input):
            #user_input += editor.read_stdin()
            #while one_inside_dict_starts_with(dictionary, user_input):
                #if user_input in dictionary:
                    #minibar(f' ( Processing command: {_escape(user_input)} )')
                    #rv = dictionary[user_input](editor)
                    #minibar('')
                    #if rv and rv != 'insert':
                        #return rv
                    #break
            #else:
                #minibar(f' ( Invalid command: {_escape(user_input)} )')
        #else:
            #minibar(f' ( Invalid command: {_escape(user_input)} )')
#
        #user_input = get_a_key()
        #minibar('')

