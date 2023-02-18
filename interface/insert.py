from vy.keys import C_C, _escape, C_J
from vy.interface.helpers import one_inside_dict_starts_with

def loop(editor):
    curbuf = editor.current_buffer
    def get_a_key():
        #completions, lengh = curbuf.completer()
        #editor.screen.minibar_completer(*curbuf.completer())
        return editor.read_stdin()

    minibar = editor.screen.minibar
    dictionary = editor.actions.insert

    while True:
        user_input = get_a_key()
        #editor.screen.minibar_completer.give_up()
        minibar('')

        if user_input in dictionary:
            minibar(f' ( Processing command: {_escape(user_input)} )')
            rv = dictionary[user_input](editor)
            minibar('')
            if rv and rv != 'insert':
                return rv

        elif user_input.isprintable() or user_input.isspace():
            curbuf.insert(user_input)

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
