try:
    from .pygments_lexer import view
except ImportError:
    from .simple_lexer import view

SET_DEF = '\x1b[0m'
def get_rows_needed(number):
    if number < 800:
        return 3
    elif number < 9800:
        return 4
    elif number < 99800:
        return 5
    elif number < 999980:
        return 6
    return len(str(number))

def cursor_switch_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
    if on_lin != cursor_lin:
        return expandtabs_numbered(tab_size, max_col, text, on_lin, -1 , -1)
    else:
        return expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col)

def expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
    number = str(on_lin).rjust(get_rows_needed(on_lin)) + ': '
    retval = list()
    line  = '\x1b[00;90;40m' + number + SET_DEF

    on_col = len(number)
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

        if on_col ==  max_col:
            line += '\x1b[0m'
            retval.append(line)
            line = '\x1b[90;40m' + ' ' * len(number)+ SET_DEF
            cursor_col  = cursor_col - (max_col - len(number))
            on_col = len(number)
            esc_flag = False

        cursor_flag = bool((on_col, on_lin) == (cursor_col, cursor_lin))
        if cursor_flag:
            line += '\x1b[5;7m'

        if char == '\t':
            nb_of_tabs =  tab_size - (on_col % tab_size)
            line += ' ' * nb_of_tabs
            on_col += nb_of_tabs
            cursor_col += (nb_of_tabs-1)
        else:
            on_col += 1
            line += char
        if cursor_flag:
            line += '\x1b[25;27m'

    retval.append(line + (' ' * (max_col - on_col)))
    return retval

def cursor_switch(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
    if on_lin != cursor_lin:
        return expandtabs(tab_size, max_col, text, on_lin, -1 , -1)
    else:
        return expandtabs(tab_size, max_col, text, on_lin, cursor_lin, cursor_col)

def expandtabs(tab_size, max_col, text, on_lin, cursor_lin, cursor_col):
    retval = list()
    line  = SET_DEF

    on_col = 1
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

        if on_col ==  max_col:
            line += '\x1b[0m'
            retval.append(line)
            line = SET_DEF
            cursor_col  = cursor_col - max_col + 1
            on_col = 1
            esc_flag = False

        cursor_flag = bool((on_col, on_lin) == (cursor_col, cursor_lin))
        if cursor_flag:
            line += '\x1b[5;7m'

        if char == '\t':
            nb_of_tabs =  tab_size - (on_col % tab_size)
            line += ' ' * nb_of_tabs
            on_col += nb_of_tabs
            cursor_col += (nb_of_tabs-1)
        else:
            on_col += 1
            line += char
        if cursor_flag:
            line += '\x1b[25;27m'

    retval.append(line + (' ' * (max_col - on_col)))
    return retval

class WindowGenerator(view):
    def __init__(self, set_number=True, set_wrap=False, set_tabsize=4, **kwargs):
        self.set_wrap = set_wrap
        self.set_number = set_number
        self.set_tabsize = set_tabsize
        super().__init__(**kwargs)

    def gen_window(self, max_col, min_lin, max_lin):
        cursor_lin, cursor_col = self.cursor_lin_col
        wrap = self.set_wrap
        if self.set_number:
            switch = cursor_switch_numbered
        else:
            switch = cursor_switch
        tab_size = self.set_tabsize
        lexed_lines = self.lexed_lines # Get a copy (descriptor)
        #virtuel = 0
        for on_lin in range(min_lin, max_lin):
            try:
                pretty_line = lexed_lines[on_lin]
            except IndexError:
                default = '~' + ((max_col-1) * ' ')
                while True:
                    yield default
            to_print = switch(tab_size, max_col, pretty_line, on_lin, cursor_lin, cursor_col)
            if wrap:
                #virtuel += len(to_print)
                #free = max_lin - (min_lin + virtuel)
                #if on_lin + free  < cursor_lin + 1:
                #    yield False
                yield from to_print
            else:
                yield to_print[0]
