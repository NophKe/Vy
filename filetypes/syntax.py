from pygments.token import (Keyword, Name, Comment, String, Error, Number, Operator, 
                                                    Generic, Token, Whitespace, Text)
from .ansiformat import ansiformat
set_def = '\x1b[0m'

#from pygments.console import ansiformat

from pygments.lexers import guess_lexer_for_filename
from pygments.util import  ClassNotFound
from functools import lru_cache, cache
from itertools import chain, repeat
#from multiprocessing import Process, Pipe


#def proc_away(func, arg_tup):
#    child, parent = Pipe()
#    def inner():
#        child.send(func(*arg_tup))
#    proc = Process(target=inner, args=arg_tup)
#    proc.start()
#    return parent

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
        rv = list()
        retval = list()
        rv.append('\x1b[00;90;40m' + number + set_def )

        on_col = len(number) - 1
        cursor_col += on_col - 1
        esc_flag = False
        cursor_flag = False

        for char in text:
            if esc_flag and char != 'm':
                rv.append(char)
                continue
            if char == '\x1b':
                esc_flag = True
                rv.append(char)
                continue
            if esc_flag and char == 'm':
                esc_flag = False
                rv.append(char)
                continue
            if (on_col, on_lin) == (cursor_col, cursor_lin) and not esc_flag:
                rv.append('\x1b[5;7m')
                cursor_flag = True

            if (on_col, on_lin) != (cursor_col, cursor_lin) and cursor_flag:
                rv.append('\x1b[25;27m')

            if on_col ==  max_col -1:
                rv.append('\x1b[0m')
                retval.append(''.join(rv))
                rv = list()
                rv.append('\x1b[90;40m' + ' ' * len(number)+ set_def)
                on_col = len(number) -1
                esc_flag = False
            elif esc_flag  and char == 'm': 
                esc_flag = False
                rv.append(char)
            elif char == '\t':
                nb_of_tabs =  tab_size - (on_col % tab_size)
                rv.append(' ' * nb_of_tabs)
                on_col += nb_of_tabs
            else:
                if not esc_flag:
                    on_col += 1
                rv.append(char)
        retval.append(''.join(rv) + (' ' * (max_col - on_col - 1)))
        return retval

def fast_expandtabs(tab_size, max_col, text):
    rv = list()
    on_col = 0
    esc_flag = False

    for char in text:
        if on_col ==  max_col :
            rv.append('\x1b[0m')
            return ''.join(rv)
            
        if char == '\x1b':
            esc_flag = True
            rv.append(char)
            continue
        elif esc_flag  and char == 'm': 
            esc_flag = False
            rv.append(char)
            continue
        elif char == '\t':
            nb_of_tabs =  tab_size - (on_col % tab_size)
            rv.append(' ' * nb_of_tabs)
            on_col += nb_of_tabs
        else:
            if not esc_flag:
                on_col += 1
            rv.append(char)

    return ''.join(rv) + (' ' * (max_col - on_col))

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
        #if hasattr(self, '_pipe_to_lexed_lines') and self._pipe_to_lexed_lines.poll():
            #self._lexed_hash, self._lexed_lines = self._pipe_to_lexed_lines.recv() 

        #if not hasattr(self,'_lexed_hash')  or self._lexed_hash != self._string.__hash__():
            #provider = self.gen_fast_lexed_line
            #self._pipe_to_lexed_lines = proc_away(lambda: (hash(self._string), self.lexed_lines), ())

        provider = self.gen_lexed_line

        max_index = max_lin + min_lin
        generator = provider( max_col, min_lin, max_lin, self.set_wrap)
        default = repeat( '~'+(' '*(max_col-1)))

        for index, item in enumerate(chain(generator,default)):
            if index < max_lin:
                yield item
            else:
                break

    def gen_fast_lexed_line(self, max_col, min_lin, max_lin, set_wrap):
        chars_to_print = 0
        line = ''
        on_lin = 0
        tab_size = self.set_tabsize
        
        for offset, tok, val in self.lexer.get_tokens_unprocessed(self._string):
            colorize = _colorize(tok)

            for token_line in val.splitlines(True):
                nl_flag = token_line.endswith('\n')
                if nl_flag:
                    token_line = token_line[:-1] + ' '

                len_to_add = len(token_line)
                
                if (offset + len_to_add) >= self.cursor >= offset:
                    cur_pos = (self.cursor - offset)
                    if cur_pos > len_to_add :
                        token_line = token_line[:cur_pos] + '\x1b7\x1b[7;5m \x1b[25;27m'
                    elif cur_pos < len_to_add:
                        token_line = token_line[:cur_pos] + '\x1b7\x1b[7;5m' + token_line[cur_pos] + '\x1b[25;27m' + token_line[cur_pos+1:]

                if nl_flag:
                    if on_lin  > min_lin:
                        yield fast_expandtabs(tab_size, max_col, line + colorize(token_line) )
                    on_lin += 1
                    chars_to_print = 0
                    line = ''
                    offset += len_to_add + chars_to_print
                    continue
                elif chars_to_print > max_col:
                    continue
                else:
                    line += colorize(token_line)
                    chars_to_print += len_to_add
                    continue
        else:
            if line:
                yield fast_expandtabs(tab_size, max_col, line )

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
    
    def gen_lexed_line(buff, max_col, min_lin, max_lin, wrap):
        cursor_lin, cursor_col = buff.cursor_lin_col
        for on_lin, pretty_line in enumerate(buff.lexed_lines):
            if on_lin > min_lin:
                to_print = switch(buff.set_tabsize, max_col, pretty_line, on_lin, cursor_lin, cursor_col)
                if wrap:
                    yield from to_print
                else:
                    yield to_print[0]
            else:
                if on_lin < min_lin:
                    continue
