from vy.keys import C_C, _escape, C_J
from vy.interface.helpers import one_inside_dict_starts_with

from jedi import Script
#from threading import Thread

def loop(editor):

    def get_a_key():
        curbuf = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        completions = Script(code=curbuf.string)
        completions = completions.complete(line=lin+1, column=col-1)
        if completions:
            lengh = completions[0].get_completion_prefix_length()
        else:
            lengh = 0
        completions = [item.name_with_symbols for item in completions if hasattr(item, 'name_with_symbols')]
        editor.screen.minibar_completer(completions, prefix=lengh)
        return editor.read_stdin()

    curbuf = editor.current_buffer
    minibar = editor.screen.minibar
    dictionary = editor.actions.insert

    while True:
        user_input = get_a_key()
        minibar('')

        if user_input in dictionary:
            minibar(f' ( Processing command: {_escape(user_input)} )')
            rv = dictionary[user_input](editor)
            minibar('')
            if rv and rv != 'insert':
                editor.screen.minibar_completer()
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
                        editor.screen.minibar_completer()
                        return rv
                    break
            else:
                minibar(f' ( Invalid command: {_escape(user_input)} )')
        else:
            minibar(f' ( Invalid command: {_escape(user_input)} )')
