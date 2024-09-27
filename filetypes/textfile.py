from vy.global_config import DEBUG
from threading import Thread
from vy.filetypes.basefile import BaseFile

class Thread(Thread):
    def __repr__(self):
        return 'Lexer Thread' + super().__repr__()

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
        self._lexing_state = '(lexer not started'
        Thread(target=self._lex_away, args=(), name=f'{repr(self)}._lex_away()', daemon=True).start()

    def _lex_away(self):
        from vy.filetypes.lexer import guess_lexer, get_prefix
        lexer = guess_lexer(self.path, self.string)
        local_dict = self._lexed_cache
        local_lexed = self._lexed_lines
        cancel_handler = self._async_tasks
        cancel_request = self._async_tasks.must_stop.is_set

        while True:
            times_we_tried = 0
            while not self._lock.acquire(blocking=False):
                times_we_tried += 1
                self._lexing_state = f'(lexer tried to start {times_we_tried} times)'
                from time import sleep
                sleep(0)
                pass
            else:
                self._lexing_state = 'string locking'
                cancel_handler.notify_working()
                string = self._string or ''.join(self._splited_lines)
                assert string, self._test_all_assertions()
                self._lock.release()
                
            line = ''

            if cancel_request():
                self._lexing_state = 'needs to stop 1'
                cancel_handler.notify_stopped()
                continue

            for off, tok, val in lexer(string):
                if cancel_request():
                    self._lexing_state = 'needs to stop 2'
                    break
                tok = get_prefix(tok)
                if '\n' in val:
                    for token_line in val.splitlines(True):
                        if token_line.endswith('\n'):
                            line += tok + token_line[:-1] + ' \x1b[97;22m'
                            local_lexed.append(line)
                            line = ''                            
                        else:
                            line += tok + token_line + '\x1b[97;22m'
                else:
                    line += tok + val + '\x1b[97;22m'
            else:
                if line and line != tok: #No eof
                    local_lexed.append(line)

            if 'stop' not in self._lexing_state:
                self._lexing_state = 'cache it all'
                for raw, lexed in zip(string.splitlines(True), local_lexed):
                    if cancel_request():
                        self._lexing_state = 'needs to stop 3'
                        break
                    local_dict[raw] = lexed
                
            if 'stop' not in self._lexing_state:
                self._lexing_state = '(lexing done)'
            cancel_handler.notify_stopped()
            self._lexed_lines.clear()
    
    if DEBUG:
        @property
        def footer(self):
            return self._lexing_state + super().footer

    def get_raw_screen(self, min_lin, max_lin):
        # This method does not take the internal lock allowing
        # the screen to asynchronously visit the buffer content.
        #
        # Any case of failure will be turned into a RuntimeError
        # to signal the screen to give up and retry later.
        raw_line_list = list()
        cancel_request = self._async_tasks.must_stop.is_set

        try:
            cursor_lin, cursor_col = self._cursor_lin_col
        except ValueError:
            raise RuntimeError # (is None) buffer in inconsistant state

        if not self._splited_lines:
            raise RuntimeError # (is empty) buffer in inconsistant state

        local_split = self._splited_lines
        try:
            for on_lin in range(min_lin, max_lin):
                if cancel_request():
                    raise RuntimeError
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
