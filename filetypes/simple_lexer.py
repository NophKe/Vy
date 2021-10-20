from .motions import Motions

class view(Motions):
    @property
    def lexed_lines(self):
        if not hasattr(self,'_lexed_hash')  or\
        self._lexed_hash != self._string.__hash__():
            retval = [f'{line[:-1]} ' for line in self._string.splitlines(True)]
            self._lexed_hash, self._lexed_lines = hash(self._string) , retval
        return self._lexed_lines
