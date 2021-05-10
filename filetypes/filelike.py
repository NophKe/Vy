class FileLike:
    def write(self, text):
        assert isinstance(text, str)
        if text:
            self.string = self._string[:self.cursor] + text + self._string[self.cursor + len(text):]
            self.cursor = self.cursor + len(text)

    def getvalue(self):
        return self._string

    def read(self, nchar= -1):
        if nchar == -1:
            rv = self._string[self.cursor:]
            self.cursor = len(self.string)
        else:
            rv = self._string[self.cursor:(self.cursor + nchar)]
            self.cursor = self.cursor + nchar
        return rv

    def tell(self):
        return self.cursor

    def seek(self,offset=0, flag=0):
        assert isinstance(offset, int)
        assert isinstance(flag, int)
        if len(self._string) == 0:
            return 0
        max_offset = len(self.string) -1
        if (offset == 0 and flag == 2) or (offset > max_offset):
            self.cursor = max_offset
        elif 0 <= offset <= max_offset:
            self.cursor = offset
        else:
            breakpoint()
