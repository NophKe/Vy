""" the codes dict and ansiformat function is freely adapated from
    pygments in the console submodule
    :copyright: Copyright 2006-2020 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
try:    
    # except ImportError near the end of file
    from pygments.token import (Keyword, Name, Comment, String, Error, Number, Operator, 
                                                        Generic, Token, Whitespace, Text)
    from pygments.lexers import guess_lexer_for_filename
    from pygments.util import  ClassNotFound
    from functools import lru_cache, cache
    from itertools import chain, repeat

    set_def = '\x1b[0m'
    esc = "\x1b["

    codes = {}
    codes[""] = ""
    codes["reset"] = esc + "39;49;00m"

    codes["bold"] = esc + "01m"
    codes["faint"] = esc + "02m"
    codes["standout"] = esc + "03m"
    codes["underline"] = esc + "04m"
    codes["blink"] = esc + "05m"
    codes["overline"] = esc + "06m"

    dark_colors = ["black", "red", "green", "yellow", "blue",
                   "magenta", "cyan", "gray"]
    light_colors = ["brightblack", "brightred", "brightgreen", "brightyellow", "brightblue",
                    "brightmagenta", "brightcyan", "white"]

    x = 30
    for d, l in zip(dark_colors, light_colors):
        codes[d] = esc + "%im" % x
        codes[l] = esc + "%im" % (60 + x)
        x += 1
    del d, l, x

    codes["white"] = codes["bold"]

    def colorize(color_key, text):
        return codes[color_key] + text + codes["reset"]

    def ansiformat(attr, text):
        """
        Format ``text`` with a color and/or some attributes::

            color       normal color
            *color*     bold color
            _color_     underlined color
            +color+     blinking color
        """
        result = ''
        if attr[:1] == attr[-1:] == '*':
            result += "\x1b[01m"
            attr = attr[1:-1]
        if attr[:1] == attr[-1:] == '_':
            result += "\x1b[04m"
            attr = attr[1:-1]
        result += codes[attr] + text + "\x1b[39;49;00m"
        return result

    colorscheme = {
        Token:              '',
        Whitespace:         'gray',         Comment:            'gray',
        Comment.Preproc:    'cyan',         Keyword:            '*blue*',
        Keyword.Type:       'cyan',         Operator.Word:      'magenta',
        Name.Builtin:       'cyan',         Name.Function:      'green',
        Name.Namespace:     '_cyan_',       Name.Class:         '_green_',
        Name.Exception:     'cyan',         Name.Decorator:     'brightblack',
        Name.Variable:      'red',          Name.Constant:      'red',
        Name.Attribute:     'cyan',         Name.Tag:           'brightblue',
        String:             'yellow',       Number:             'blue',
        Generic.Deleted:    'brightred',    Text:               '', 
        Generic.Inserted:   'green',        Generic.Heading:    '**',
        Generic.Subheading: '*magenta*',    Generic.Prompt:     '**',
        Generic.Error:      'brightred',    Error:              '_brightred_',
    }
    @cache
    def _colorize(ttype):
        @cache
        def func(text):
            return ansiformat(color, text)
        for token_class in reversed(ttype.split()):
            if ttype in colorscheme:
                color = colorscheme[ttype]
            else:
                ttype = ttype.parent
        return func

    def get_rows_needed(number):
        if number < 800:
            return 3
        if number < 9800:
            return 4
        if number < 99800:
            return 5
        if number < 999980:
            return 6
        else:
            return 10

    def switch(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
        if on_lin != cursor_lin: 
            return expandtabs(tab_size, max_col, text, on_lin, -1 , -1)
        else:
            return expandtabs(tab_size, max_col, text, on_lin, cursor_lin, cursor_col)

    @cache
    def expandtabs(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
            number = str(on_lin).rjust(get_rows_needed(on_lin)) + ': '
            line = list()   # the computed final printed line
            retval = list() # the function return a list of those
                            # for line wrapping
            line  = '\x1b[00;90;40m' + number + set_def 

            on_col = len(number) - 1
            cursor_col += on_col - 1
            esc_flag = False
            cursor_flag = False

            for char in text:
                if esc_flag:
                    line += char
                    if char == 'm':
                        esc_flag = False
                    continue

                if char == '\x1b':
                    esc_flag = True
                    line += char
                    continue

                if (on_col, on_lin) == (cursor_col, cursor_lin) and not esc_flag:
                    line += '\x1b[5;7m'
                    cursor_flag = True

                if (on_col, on_lin) != (cursor_col, cursor_lin) and cursor_flag:
                    line += '\x1b[25;27m'

                if on_col ==  max_col -1:
                    line += '\x1b[0m'
                    retval.append(line)
                    line = '\x1b[90;40m' + ' ' * len(number)+ set_def
                    on_col = len(number) -1
                    esc_flag = False

                if char == '\t':
                    nb_of_tabs =  tab_size - (on_col % tab_size)
                    line += ' ' * nb_of_tabs
                    on_col += nb_of_tabs
                    cursor_col += (nb_of_tabs-1)
                else:
                    on_col += 1
                    line += char
            retval.append(line + (' ' * (max_col - on_col - 1)))
            return retval

    class view:
        def __init__(self, path=None, cursor=0):
            super().__init__()
            self.set_wrap = False
            self.set_tabsize = 4
            filename = self.path if self.path else ''
            try:
                self.lexer = guess_lexer_for_filename(filename, self._string, tabsize = self.set_tabsize, encoding='utf-8')
            except ClassNotFound:
                self.lexer = guess_lexer_for_filename('text.txt', self._string, tabsize = self.set_tabsize, encoding='utf-8')

        def gen_window(self, max_col, min_lin, max_lin):
            cursor_lin, cursor_col = self.cursor_lin_col
            wrap = self.set_wrap
            for on_lin in range(min_lin +1, len(self.lexed_lines)):
                pretty_line = self.lexed_lines[on_lin]
                to_print = switch(self.set_tabsize, max_col, pretty_line, on_lin, cursor_lin, cursor_col)
                if wrap:
                    yield from to_print
                else:
                    yield to_print[0]

        @property
        def lexed_lines(self):
            if not hasattr(self,'_lexed_hash')  or self._lexed_hash != self._string.__hash__():
                retval = list()
                line = ''
                on_lin = 0
                for offset, tok, val in self.lexer.get_tokens_unprocessed(self._string):
                    colorize = _colorize(tok)
                    for token_line in val.splitlines(True):
                        if token_line.endswith('\n'):
                            token_line = token_line[:-1] + ' '
                            retval.append(line + colorize(token_line))
                            on_lin += 1
                            line = ''
                        else:
                            line += colorize(token_line)
                if line:
                    retval.append(line)
                self._lexed_hash, self._lexed_lines = hash(self._string) , retval
            return self._lexed_lines
        
except ImportError:
    class _bogus:
        def __set__(self, value):
            pass
        def __get__(self):
            pass
    class view:
        lexed_lines = _bogus()
        set_tab_size = 4
        def gen_window(buff, max_col, lin_shift, max_lin):
            lin, col = buff.cursor_lin_col
            for index in range(lin_shift, max_lin):
                try:
                    line = buff.splited_lines[index]
                except IndexError:
                    while True:
                        yield "".expandtabs(tabsize=buff.set_tab_size).ljust(max_col, ' ')
                if lin == index:
                    if col < len(line):
                        line = line[:col] + '\x1b7\x1b[7;5m' + line[col] + '\x1b[25;27m' + line[col+1:]
                    else:
                        line = line[:col] + '\x1b7\x1b[7;5m \x1b[25;27m'
                yield line.expandtabs(tabsize=buff.set_tab_size).ljust(max_col, ' ')

        @property
        def splited_lines(self):
            if not hasattr(self, '_splited_lines') or \
                        self._hash_of_splited_lines != hash(self._string):
                self._splited_lines = list(self._string.splitlines())
                self._hash_of_splited_lines = hash(self._string)
            return self._splited_lines
