from threading import Thread
from time import sleep
from vy.filetypes.basefile import BaseFile
from vy.filetypes.completer import Completer

class TextFile(BaseFile):
    """
    This is the class that most of files buffers should use, 
    and should be preferably yielded by editor.cache[].
    Inherit from it to customize it.
    """
    modifiable = True

    def __init__(self, *args, **kwargs):
        BaseFile.__init__(self, *args, **kwargs)
        self._lexed_cache = {}
        self._lexed_lines = list()
        self._token_list = list()
        Thread(target=self._lex_away, args=(), name=f'{repr(self)}._lex_away()', daemon=True).start()
        self.completer_engine = Completer(self)

    def get_completions(self):
        return self.completer_engine.get_raw_screen()            

    def _lex_away(self):
        from vy.filetypes.lexer import guess_lexer, get_prefix
        lexer = guess_lexer(self.path, self.string)
        local_dict = self._lexed_cache
        local_lexed = self._lexed_lines
        cancel_handler = self._async_tasks
        cancel_request = self._async_tasks.must_stop

        while True:
            cancel_handler.notify_working()
            local_split = iter(self.splited_lines).__next__
            self.cursor_lin_col
            self.number_of_lin
            if cancel_request:
                cancel_handler.notify_stopped()
                continue

            line = ''
            for off, tok, val in lexer(self.string):
                if cancel_request:
                    break
                self._token_list.append(off)
                tok = get_prefix(tok)
                if '\n' in val:
                    for token_line in val.splitlines(True):
                        if token_line.endswith('\n'):
                            line += tok + token_line[:-1] + ' \x1b[97;22m'
                            local_lexed.append(line)
                            local_dict[local_split()] = line
                            line = tok
                        else:
                            line += tok + token_line + '\x1b[97;22m'
                else:
                    line += tok + val + '\x1b[97;22m'
            else:
                if line and line != tok: #No eof
                    local_dict[local_split()] = line
                    local_lexed.append(line)
            #import time
            #if round(time.time()) % 2 == 0:
                #raise IndexError
            cancel_handler.notify_task_done()
            self._token_list.clear()
            self._lexed_lines.clear()

    def get_raw_screen(self, min_lin, max_lin):
        # This method does not take the internal lock allowing
        # the screen to asynchronously visit the buffer content.
        #
        # Any case of failure will be turned into a RuntimeError
        # to signal the screen to give up and retry later.
        raw_line_list = list()

        try:
            cursor_lin, cursor_col = self._cursor_lin_col
        except ValueError:
            raise RuntimeError # (is None) buffer in inconsistant state

        if self._splited_lines:
            local_split = self._splited_lines
        else:
            raise RuntimeError # (is empty) buffer in inconsistant state

        try:
            for on_lin in range(min_lin, max_lin):
                try:
                    cur_lex = self._lexed_lines[on_lin] # Best case scenario
                except IndexError: 
                    cur_lin = local_split[on_lin]
                    # If on_lin is a valid line number, use the un-lexed line
                    cur_lex = self._lexed_cache.get(cur_lin, cur_lin.replace('\n',' '))
                    # if the line got lexed by a previous lexer pass, use the cached
                    # lexed version. Otherwise, just remove the newline character
                
                raw_line_list.append(cur_lex)
        
        except IndexError: 
            #local_split[on_lin] raised IndexError
            if not (nb_of_lines := self._number_of_lin):
                raise RuntimeError
                # buffer in inconsistent state
            
            if nb_of_lines <= on_lin:
                # on_lin  matches a valid index, this means we passed 
                # the final line of the buffer and should yield the empty line (~) 
                for _ in range(on_lin, max_lin):
                    raw_line_list.append(None)

        return cursor_lin, cursor_col, raw_line_list
