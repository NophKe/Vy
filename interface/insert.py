from vy.keys import C_C, _escape, C_J
from vy.interface.helpers import one_inside_dict_starts_with

def loop(self):
    curbuf = self.current_buffer
    minibar = self.screen.minibar
    dictionary = self.actions.insert

    while True:
        user_input = self.read_stdin()
        minibar('')

        if user_input in f'\r\n{C_J}':
            curbuf.insert_newline()

        elif user_input in dictionary:
            minibar(f' ( Processing command: {_escape(user_input)} )')
            rv = dictionary[user_input](self)
            minibar('')
            if rv and rv != 'insert':
                return rv

        elif user_input.isprintable() or user_input.isspace():
            curbuf.insert(user_input)

        elif one_inside_dict_starts_with(dictionary, user_input):
            user_input += self.read_stdin()
            while one_inside_dict_starts_with(dictionary, user_input):
                if user_input in dictionary:
                    minibar(f' ( Processing command: {_escape(user_input)} )')
                    rv = dictionary[user_input](self)
                    minibar('')
                    if rv and rv != 'insert':
                        return rv
                    break
            else:
                minibar(f' ( Invalid command: {_escape(user_input)} )')
        else:
            minibar(f' ( Invalid command: {_escape(user_input)} )')
