from vy.keys import _escape
from vy.interface.helpers import one_inside_dict_starts_with

def loop(editor):
    curbuf = editor.current_buffer
    get_a_key = editor.read_stdin
    minibar = editor.screen.minibar
    dictionary = editor.actions.insert
    last_insert = ''
    
    user_input = get_a_key()

    while True:
        if user_input in dictionary:
            minibar(f' ( Processing command: {_escape(user_input)} )')
            rv = dictionary[user_input](editor)
            minibar('')
            if rv and rv != 'insert':
                return rv

        elif user_input.isprintable() or user_input.isspace():
            curbuf.set_undo_record(True)
            curbuf.set_undo_record(False)
            curbuf.insert(user_input)
            last_insert += user_input
            while True:
                user_input = get_a_key()
                if user_input.isprintable() or user_input.isspace() \
                        and not user_input in dictionary            \
                        and not any(k.startswith(user_input) for k in dictionary):
                    curbuf.insert(user_input)
                    last_insert += user_input
                    continue
                curbuf.set_undo_record(True)
                break
            editor.registr['.'] = last_insert
            last_insert = ''
            continue

        elif one_inside_dict_starts_with(dictionary, user_input):
            user_input += editor.read_stdin()
            while one_inside_dict_starts_with(dictionary, user_input):
                if user_input in dictionary:
                    minibar(f' ( Processing command: {_escape(user_input)} )')
                    rv = dictionary[user_input](editor)
                    minibar('')
                    if rv and rv != 'insert':
                        #editor.screen.minibar_completer.give_up()
                        return rv
                    break
            else:
                #editor.screen.minibar_completer.give_up()
                minibar(f' ( Invalid command: {_escape(user_input)} )')
        else:
            #editor.screen.minibar_completer.give_up()
            minibar(f' ( Invalid command: {_escape(user_input)} )')

        user_input = get_a_key()
        minibar('')

