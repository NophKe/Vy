from vy.global_config import DEBUG
from threading import Thread
from vy.filetypes.basefile import BaseFile
from time import sleep

DELIMS = '+=#/?*<> ,;:/!%.{}()[]():\n\t\"\''

def make_word_set(string):
    accu = set()
    entry = ''
    for letter in string:
        if letter not in DELIMS:
            entry += letter
        else:
            if entry:
                accu.add(entry)
                entry = ''
    return accu

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
        self._token_list = []
        self._lexed_lines = []
        Thread(target=self._lex_away, args=(), name=f'{repr(self)}._lex_away()', daemon=True).start()

    def _lex_away(self):
        from vy.filetypes.lexer import guess_lexer, get_prefix
        lexer = guess_lexer(self.path, self.string)
        local_dict = self._lexed_cache
        local_lexed = self._lexed_lines
        cancel_handler = self._async_tasks
        cancel_request = self._async_tasks.must_stop.is_set

        while True:
            if not self._lock.acquire(blocking=False):
                sleep(0)
                continue
            
            cancel_handler.notify_working()
            self.cursor_lin_col            
            string = self._string or ''.join(self._splited_lines)
            self._lock.release()
                
            line = ''

            if cancel_request():
                cancel_handler.notify_stopped()
                continue

            for off, tok, val in lexer(string):
                if cancel_request():
                    break
                tok = get_prefix(tok)
                if '\n' in val:
                    for token_line in val.splitlines(True):
                        if token_line.endswith('\n'):
                            line += tok + token_line[:-1] + ' \x1b[97;22;24m'
                            local_lexed.append(line)
                            line = ''                            
                        else:
                            line += tok + token_line + '\x1b[97;22;24m'
                else:
                    line += tok + val + '\x1b[97;22;24m'
            else:
                if line and line != tok: #No eof
                    local_lexed.append(line)

                for raw, lexed in zip(string.splitlines(True), local_lexed):
                    if cancel_request():
                        break
                    local_dict[raw] = lexed
                else:
                    for line in self._splited_lines:
                        if cancel_request():
                            break
                        for w in make_word_set(line):
                            if w not in self.word_set:
                                self.ANY_BUFFER_WORD_SET.add(w)
                                self.word_set.add(w)
                    else:
                        for word in self.word_set.copy():
                            if cancel_request():
                                break
                            if word not in string:
                                self.word_set.remove(word)
  
                            
            cancel_handler.notify_stopped()
            self._lexed_lines.clear()
            self._token_list.clear()
    
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
            raise RuntimeError('cursor_lin_col undefined') # (is None) buffer in inconsistant state

        if not self._splited_lines:
            raise RuntimeError('_splited_lines is empty') # (is empty) buffer in inconsistant state

        local_split = self._splited_lines
        try:
            for on_lin in range(min_lin, max_lin):
                if cancel_request():
                    raise RuntimeError('cancelled')
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
                raise RuntimeError('nb_of_lin undefined')
                # buffer in inconsistent state
            
            if nb_of_lines <= on_lin:
                # on_lin  matches a valid index, this means we passed 
                # the final line of the buffer and should yield the empty line (~) 
                for _ in range(on_lin, max_lin):
                    raw_line_list.append(None)

        return cursor_lin, cursor_col, raw_line_list
