from threading import Thread
from time import sleep

from vy.filetypes.basefile import BaseFile
from vy.filetypes.completer import Completer
from vy.filetypes.lexer import guess_lexer, get_prefix

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
        self.lexer = guess_lexer(self.path, self._string)
        self._undo_proc = Thread(target=self._undo_away, args=(), daemon=True)
        self._lexer_proc = Thread(target=self._lex_away, args=(), daemon=True)
        self._lexer_proc.start()
        self._undo_proc.start()
        self._completer = None, None

    @property
    def completer_engine(self):
        with self._lock:
            engine, version = self._completer
            if version != self._string:
                engine = Completer(self)
                self._completer = engine, self.string
            return engine

    def check_completions(self):
        _, version = self._completer
        if self._string == version and self.cursor_lin_col == self._last_comp:
            return False
        return True

    def get_completions(self):
        with self._lock:
            lin, col = self.cursor_lin_col
            self._last_comp = lin, col
            completions = self.completer_engine.complete(line=lin+1, column=col-1)
            if completions:
                return completions
            else:
                return [], 0

    def _undo_away(self):
        while True:
            sleep(5)
            self.cancel.notify_working()
            self.set_undo_point()
            self.cancel.notify_stopped()

    def _lex_away(self):
        local_dict = self._lexed_cache
        local_lexed = self._lexed_lines

        while True:
            self.cancel.notify_working()
            local_split = iter(self.splited_lines).__next__
            self.cursor_lin_col
            self.number_of_lin
            if self.cancel:
                self.cancel.notify_stopped()
                continue

            line = ''
            for _, tok, val in self.lexer(self.string):
                if self.cancel: 
                    break
                tok = get_prefix(tok)
                if '\n' in val:
                    for token_line in val.splitlines(True):
                        if token_line.endswith('\n'):
                            line += tok + token_line[:-1] + ' \x1b[39;22m'
                            local_lexed.append(line)
                            local_dict[local_split()] = line
                            line = tok
                        else:
                            line += tok + token_line + '\x1b[39;22m'
                else:
                    line += tok + val + '\x1b[39;22m'
            else:
                if line and line != tok: #No eof
                    local_dict[local_split()] = line
                    local_lexed.append(line)

            self.cancel.notify_stopped()
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
            raise RuntimeError # buffer in inconsistant state

        if self._splited_lines:
            local_split = self._splited_lines
        else:
            raise RuntimeError # buffer in inconsistant state

        try:
            for on_lin in range(min_lin, max_lin):
                try:
                    cur_lex = self._lexed_lines[on_lin] # Best case scenario
                except IndexError: 
                    # If on_lin is a valid line number, use the un-lexed line
                    # but if the line got lexed by a previous lexer pass, use the cached
                    # lexed version. Otherwise, just remove the newline character
                    cur_lin = local_split[on_lin]
                    cur_lex = self._lexed_cache.get(cur_lin, cur_lin.replace('\n',' '))
                raw_line_list.append(cur_lex)
        except IndexError:
            # check if number_of_lin is valid first otherwise give up.
            # if we are sure on_lin  matches a valid index, this means we passed 
            # the final line of the buffer and should yield the empty line (~) 
            # If on_lin is a valid index, but raises anyway, then this means the
            # lexer has not yet reached that line or self._lexed_lines or 
            # self._splited_lines got .clear()ed by an other thread
            if self._number_of_lin and self._number_of_lin <= on_lin:
                for _ in range(on_lin, max_lin):
                    raw_line_list.append(None)
            else:
                raise RuntimeError 

        return cursor_lin, cursor_col, raw_line_list
