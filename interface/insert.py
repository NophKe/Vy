from threading import Thread
from multiprocessing import Process

from ..keys import C_C, _escape
from ..console import stdin_no_echo
from .helpers import one_inside_dict_starts_with

def loop(self):
    curbuf = self.current_buffer
    screen = self.screen
    dictionary = self.actions.insert
    dictionary[C_C] = lambda: 'normal'

    first = True
    show = lambda : None
    show.kill = show
    show.join = lambda x: None
    with stdin_no_echo():
        while True:
#           queue = curbuf._lexer_queue if not curbuf._lexed_lines else None
            new_show = Thread(target=self.show_screen, args=(True,), daemon=True)
            new_show.start()
            show.join(0.01)
            #show.kill()
            show = new_show
            user_input = self.read_stdin()

            if user_input in '²\x1b':
                curbuf.set_undo_point()
                #show.join()
                return 'normal'

            if user_input == '\r':
                #show.kill()
                curbuf.insert('\n')
                self.screen.infobar(' (newline inserted, setting undo point)')
                curbuf.set_undo_point()
                continue

            if user_input.isprintable() or user_input == ' ':
                #show.kill()
                curbuf.insert(user_input)
                continue

            if user_input in dictionary:
                #show.kill()
                self.screen.infobar(f' (Processing command: {_escape(user_input)} )')
                self.screen.minibar('')
                rv = dictionary[user_input]()
                if rv and rv != 'insert':
                    #curbuf.start_undo_record()
                    return rv
                continue

            if one_inside_dict_starts_with(dictionary, user_input):
                user_input += self.read_stdin()
                while one_inside_dict_starts_with(dictionary, user_input):
                    if user_input in dictionary:
                        #show.kill()
                        self.screen.infobar(f' (Processing command: {_escape(user_input)} )')
                        self.screen.minibar('')
                        rv = dictionary[user_input]()
                        if rv and rv != 'insert':
                            #curbuf.start_undo_record()
                            return rv
                        break
