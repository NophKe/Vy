from pygments.token import Keyword, Name, Comment, String, Error, Number, Operator, Generic, Token, Whitespace
from pygments.console import ansiformat
from itertools import chain, repeat

from pygments.lexers import guess_lexer_for_filename
from pygments.util import  ClassNotFound


class Printer:
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
        Generic.Deleted:    'brightred',
        Generic.Inserted:   'green',        Generic.Heading:    '**',
        Generic.Subheading: '*magenta*',    Generic.Prompt:     '**',
        Generic.Error:      'brightred',    Error:              '_brightred_',
    }

    def lexer(self):
        if not self._lexer:
            filename = self.path if self.path else ''
            try:
                self._lexer = guess_lexer_for_filename(filename, self.getvalue(), tabsize = self.tab_size, encoding='utf-8')
            except ClassNotFound:
                self._lexer = guess_lexer_for_filename('text.txt', self.getvalue(), tabsize = self.tab_size, encoding='utf-8')
        return self._lexer

    def _colorize(self, ttype):
        def func(text):
            return ansiformat(color, text)
        for token_class in reversed(ttype.split()):
            if ttype in self.colorscheme:
                color = self.colorscheme[ttype]
            else:
                ttype = ttype.parent
        return func

    def expandtabs(self,max_col, text):
        rv = list()
        on_col = 0
        tab_size = self.tab_size
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

    def gen_lexed_line(self, max_col, min_lin):
        chars_to_print = 0
        line = ''
        on_lin = 0
        
        for offset, tok, val in self.lexer().get_tokens_unprocessed(self._string):
            colorize = self._colorize(tok)

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
                    if on_lin  < min_lin:
                        yield ''
                    else:
                        yield self.expandtabs(max_col, line + colorize(token_line) )
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
                yield self.expandtabs(max_col, line )

    def gen_window(self, col_shift, max_col, lin_shift, max_lin):
        max_index = max_lin + lin_shift
        for index, item in enumerate(chain(self.gen_lexed_line(max_col, lin_shift),
                                           repeat( '~'+(' '*(max_col-1))))):
            if index < lin_shift:
                continue
            elif lin_shift <= index <= max_index:
                yield item
            elif index > max_index:
                break
