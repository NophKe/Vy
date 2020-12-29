from pygments.token import Keyword, Name, Comment, String, Error, Number, Operator, Generic, Token, Whitespace
from pygments.console import ansiformat
from pygments.lexers import guess_lexer_for_filename
from pygments.util import  ClassNotFound

from functools import lru_cache
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


def _colorize(ttype):
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

@lru_cache(50)
def expandtabs(tab_size, max_col, text, on_lin):
    number = str(on_lin).rjust(get_rows_needed(on_lin)) + ': '
    number = number
    rv = list()
    retval = list()
    rv.append(number)
    on_col = len(number) - 1
    esc_flag = False
    
    for char in text:
        if on_col ==  max_col -1:
            rv.append('\x1b[0m')
            retval.append(''.join(rv))
            rv = list()
            rv.append(' ' * len(number))
            on_col = len(number) -1
            esc_flag = False
            
        if char == '\x1b':
            esc_flag = True
            rv.append(char)

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
    retval.append(''.join(rv) + (' ' * (max_col - on_col)))
    return retval 

def gen_lexed_line(buff, max_col, min_lin, wrap):
    if not buff.lexer:
        filename = buff.path if buff.path else ''
        try:
            buff.lexer = guess_lexer_for_filename(filename, buff.getvalue(), tabsize = buff.tab_size, encoding='utf-8')
        except ClassNotFound:
            buff.lexer = guess_lexer_for_filename('text.txt', buff.getvalue(), tabsize = buff.tab_size, encoding='utf-8')

    line = ''
    on_lin = 0
    
    for offset, tok, val in buff.lexer.get_tokens_unprocessed(buff._string):
        colorize = _colorize(tok)

        for token_line in val.splitlines(True):
            nl_flag = token_line.endswith('\n')
            if nl_flag:
                token_line = token_line[:-1] + ' '

            len_to_add = len(token_line)
            
            if (offset + len_to_add) >= buff.cursor >= offset:
                cur_pos = (buff.cursor - offset)
                if cur_pos > len_to_add :
                    token_line = token_line[:cur_pos] + '\x1b7\x1b[7;5m \x1b[25;27m'
                elif cur_pos < len_to_add:
                    token_line = token_line[:cur_pos] + '\x1b7\x1b[7;5m' + token_line[cur_pos] + '\x1b[25;27m' + token_line[cur_pos+1:]

            if nl_flag:
                if on_lin > min_lin:
                    to_print = expandtabs(buff.tab_size, max_col, line + colorize(token_line), on_lin )
                    if wrap:
                        yield from to_print
                    else:
                        yield to_print[0]

                on_lin += 1
                line = ''
                offset += len_to_add
            else:
                if on_lin < min_lin:
                    continue
                line += colorize(token_line)
    else:
        if line:
            yield expandtabs(tab_size, max_col, line, on_lin )