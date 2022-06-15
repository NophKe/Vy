from vy.keys import C_C, _escape, C_J
from vy.interface.helpers import one_inside_dict_starts_with

def loop(self):
    curbuf = self.current_buffer
    screen = self.screen
    dictionary = self.actions.insert

    while True:
        user_input = self.read_stdin()
        screen.minibar('')

        if user_input in f'\r\n{C_J}':
            curbuf.insert('\n')
            screen.minibar(f'( Newline inserted, setting undo point )')
            curbuf.set_undo_point()

        elif user_input in dictionary:
            screen.minibar(f' ( Processing command: {_escape(user_input)} )')
            rv = dictionary[user_input](self)
            screen.minibar('')
            if rv and rv != 'insert':
                return rv
            continue

        elif user_input.isprintable() or user_input.isspace():
            curbuf.insert(user_input)
            continue

        elif one_inside_dict_starts_with(dictionary, user_input):
            user_input += self.read_stdin()
            while one_inside_dict_starts_with(dictionary, user_input):
                if user_input in dictionary:
                    screen.minibar(f' ( Processing command: {_escape(user_input)} )')
                    rv = dictionary[user_input](self)
                    screen.minibar('')
                    if rv and rv != 'insert':
                        return rv
                    break
            else:
                if user_input.isprintable():
                    curbuf.insert(user_input)
                else:
                    screen.minibar(f' ( Invalid command: {_escape(user_input)} )')
        else:
            raise RuntimeError("This line should never be reached")
