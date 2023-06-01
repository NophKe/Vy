from vy.keys import _escape

from vy.interface.helpers import one_inside_dict_starts_with
from vy import keys as k

def monoline_loop(editor):
    last_insert = ''
    while (key_press := editor.read_stdin()).isprintable():
        editor.current_buffer.undo_list.skip_next()
        editor.current_buffer.insert(key_press)

    if last_insert.strip():
        editor.registr['.'] = last_insert
    return key_press

def init(editor):
    global get_a_key, minibar, dictionary, minidict
    get_a_key = editor.read_stdin
    minibar = editor.screen.minibar
    dictionary = editor.actions.insert
    
def loop(editor):
    editor.screen.minibar_completer.set_callbacks(
                    lambda: editor.current_buffer.get_completions(), 
                    lambda: editor.current_buffer.check_completions())
    mode = 'insert'
    while mode in ('insert', 'completion'):
        if mode == 'completion':
            return 'completion'
        else:
            user_input = monoline_loop(editor) 
            cancel_minibar = minibar(f' __ Processing command: {_escape(user_input)} __')
            try:
                action = dictionary[user_input]
            except KeyError:
                minibar(f' ( Invalid command: {_escape(user_input)} )')
            else:
                mode = action(editor) or 'insert'
                cancel_minibar()
    
    editor.screen.minibar_completer.give_up()
    return mode
