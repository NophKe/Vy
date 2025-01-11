"""
    ***************************
    ****    Motions        ****
    ***************************

In vim, dgd is valid but d<page-down> is not!  Why?  I *really* want
d<page-up> to work!  And for now it does not in vim and neither in  Vy.
Why does Vim exhibit such a behaviour?
 
My guess is some motion are window-related while others buffer or cursor
related.  And window-related motions are not consistant!  By  this I mean a
window redraw may change last shown line on screen for example.

This mean that an action like d<page-down> to work would need that  relative
cursor position on the screen and cursor position on the  text itself should
have properties linking them that may not change asynchronously because of a
window redraw by example.
 
 For now in Vy things are a bit more complicated, *true* motions that can be
 used as operator are buffer dependent and implemented by dict
 Basefile.motion_commands.  This is work in progress.
 
 TODO: But for now Basefile.motion_commands contains methods that receive  a
 Basefile instance self.  Those new kind of actions would receive a editor
 instance and need to resolve editor.current_buffer....  should be moved to
 here.

"""

from vy.keys import _escape
from vy import keys as _k
from vy.editor import _Editor

class _motion:
    v_header = """
    This command is part of visual mode «motion» commands.

    [SYNTAX]      ["{register}] [{count}] %s
    aliases: %s
    ---
    NOTE: {register} will be ignored."""
    
    i_header = """
    This command is part of insert mode «motion» commands.

    [SYNTAX]      %s
    aliases: %s"""
    
    n_header = """
    This command is part of normal mode «motion» commands and can be used as an
    operator for {command} or single with an optionnal {count}.

    [SYNTAX]      ["{register}] [{count}] [{command}] [{count}] %s
    [SYNTAX]      ["{register}] [{count}] %s
    aliases: %s
    ---
    NOTE: if used without {command}, {register} is ignored."""

    category = "motion"
    def update_func(self, alias, func):
        n_alias: list = list()
        v_alias: list = list()
        i_alias: list = list()

        for item in alias.split(" "):
            if item.startswith('v_')  :
                v_alias.append(item.removeprefix('v_'))
            elif item.startswith('i_'):
                i_alias.append(item.removeprefix('i_'))
            else:
                n_alias.append(item)

        separator = '\n    ' + '-' * 68 #+ '\n'
        header = separator
        if n_alias:
            header += self.n_header % (_escape(n_alias[0]) , _escape(n_alias[0]),
                                    ' '.join(_escape(item) for item in n_alias).ljust(60))
            header += separator
        if v_alias:
            header += self.v_header % (_escape(v_alias[0]) ,
                                    ' '.join(_escape(item) for item in v_alias).ljust(60))
            header += separator
        if i_alias:
            header += self.i_header % (_escape(i_alias[0]) ,
                                    ' '.join(_escape(item) for item in i_alias).ljust(60))
            header += separator
        if any((i_alias, n_alias, v_alias,)):
            header += '\n'

        if func.__doc__:
            func.__doc__ += """
    ---
    NOTE: This may be recorded in jump list."""
        func.motion = True
        func.stand_alone = func.with_args  = func.full = func.atomic = False

        func.n_alias = n_alias if n_alias else None
        func.c_alias = None
        func.v_alias = v_alias if v_alias else None
        func.i_alias = i_alias if i_alias else None

        func.__doc__ = header + (func.__doc__ or '')
        return func

    def __call__(self, alias):
        return lambda func : self.update_func(alias, func)

_motion_commands = _motion()

@_motion_commands(f'i_{_k.left} {_k.left} h')
def do_normal_h(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one character left.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin, col-count)

@_motion_commands(f'j + \n \r {_k.C_J} i_{_k.C_M} {_k.C_N} '
                  f'i_{_k.down} {_k.down}'
                 )
def do_normal_j(editor: _Editor, reg=None, part=None, arg=None, count=1):
    """
    Move one line down.
    """
    cb = editor.current_buffer
    cb.cursor_lin_col = (cb.current_line_idx+count, 0)

@_motion_commands(f'i_{_k.up} {_k.up} {_k.C_P} k -')
def do_normal_k(editor, reg=None, part=None, arg=None, count=1):
    """
    Move one line up.
    """
    lin, _ = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin-count, 0)

@_motion_commands(f'l i_{_k.right} {_k.space} {_k.right}')
def do_normal_l(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one character right.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin, col+count)

@_motion_commands('0')
def do_normal_zero(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to beginning of line.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_begining_of_line()

@_motion_commands('e')
def do_normal_e(editor: _Editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor to the end of word.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_end_of_word()

@_motion_commands('E')
def do_normal_E(editor: _Editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor to the end of WORD.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_end_of_word()
    
@_motion_commands(f'$ {_k.end} i_{_k.end}')
def do_normal_dollar(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to end of line.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_end_of_line()

@_motion_commands('G')
def do_normal_G(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to the end of file.
    ---
    NOTE:
    This does not correspond to the vim behaviour. In vim, G move to the last
    line on the first collumn, whereas dG deletes till the end of last line.
    In Vy, G is allways last collumn, last line.
    ---
    """
    curbuf = editor.current_buffer
    curbuf.cursor = len(curbuf) - 1

@_motion_commands('gg')
def do_normal_gg(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to first line first character.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = 0

@_motion_commands('_')
def do_normal_underscore(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to the first character of the current line.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_first_non_blank_char_in_line()

@_motion_commands(f'B i_{_k.C_left} {_k.C_left}')
def do_normal_B(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one WORD backwards.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_normal_B()

@_motion_commands(f'b i_{_k.S_left} {_k.S_left}')
def do_normal_b(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one word backwards.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_previous_delim()

@_motion_commands(f'W i_{_k.C_right} {_k.C_right}')
def do_normal_W(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one WORD right.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_next_WORD()

@_motion_commands(f'w i_{_k.S_right} {_k.S_right}')
def do_normal_w(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one word forward.
    """
    with editor.current_buffer as curbuf:
        for _ in range(count):
            curbuf.cursor = curbuf.find_next_delim()

@_motion_commands(f'{_k.page_down} i_{_k.page_down} {_k.C_B}')
def do_page_down(editor: _Editor, reg=None, part=None, arg=None, count=1):
    """
    If the cursor is on the higher part of the screen, the cursor goes to 
    the middle of the current windows.
    If the cursor is on the botton part of the screen, the cursor goes to 
    the last line of the current windows.
    
    If on the last displayed line, scrolls the text one page down.
    ---
    NOTE: Not Vim behaviour.
    ---
    """
    curbuf = editor.current_buffer
    curwin = editor.current_window
    first, last = curwin.shown_lines
    last -= 1
    page_size = last - first
    lin, col = curbuf.cursor_lin_col
    middle = first + (page_size // 2)
    
    
    if lin < middle:
        curbuf.cursor_lin_col = (middle, 0)
    elif lin < last:
        curbuf.cursor_lin_col = (last, 0)
    else:
        curbuf.cursor_lin_col = (last+page_size-1, 0)

    if curbuf.current_line_idx == curbuf.number_of_lin - 1:
        editor.actions.normal('zz')
        
@_motion_commands(f'{_k.page_up} i_{_k.page_up} {_k.C_F}')
def do_page_up(editor, reg=None, part=None, arg=None, count=1):
    """
    If the cursor is on the higher part of the screen, the cursor goes to 
    the middle of the current windows.
    If the cursor is on the botton part of the screen, the cursor goes to 
    the first line of the current windows.
    
    If on the first displayed line, scrolls the text one page up.
    ---
    NOTE: Not Vim behaviour.
    ---
    """
    curbuf = editor.current_buffer
    curwin = editor.current_window
    first, last = curwin.shown_lines
    last -= 1
    page_size = last - first
    lin, col = curbuf.cursor_lin_col
    middle = first + (page_size // 2)
    
    
    if lin > middle:
        curbuf.cursor_lin_col = (middle, 0)
    elif lin > first:
        curbuf.cursor_lin_col = (first, 0)
    else:
        curbuf.cursor_lin_col = (first - page_size, 0)

@_motion_commands("n")
def do_normal_n(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor to next occurrence of last searched text.
    """
    needle = editor.registr['/']
    if not needle:
        raise editor.MustGiveUp(' ( No previous search. )')

    curbuf = editor.current_buffer
    find = curbuf.string.find
    current_offset = curbuf.cursor
    
    offset = find(needle, current_offset) 
    if offset == current_offset:
        offset = find(needle, current_offset + 1)

    if offset == -1:
        editor.screen.minibar(f'String: «{needle}» not found, retrying from first line.')
        offset = find(needle)

    if offset == -1:
        editor.screen.minibar(f'String: «{needle}» not found!')
    else:
        with curbuf._lock:
            curbuf.cursor = offset    
            editor.actions.normal('zz')
            editor.screen.recenter()
        
    
@_motion_commands("N")
def do_normal_N(editor: _Editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor to previous occurrence of last searched text.
    """
    needle = editor.registr['/']
    curbuf = editor.current_buffer
    current_offset = curbuf.cursor
    
    if needle:
        offset = curbuf.string.rfind(needle, 0, curbuf.cursor)

        if offset == current_offset:
            offset = curbuf.string.rfind(needle, 0, curbuf.cursor - 1)
    
        if offset == -1:
            editor.screen.minibar('String not found: back to the end.')
            offset = curbuf._string.rfind(needle)
    
        if offset == -1:
            editor.screen.minibar('String not found!')
            return 'normal'
    
        curbuf.cursor = offset    
        editor.actions.normal('zz')
    else:
        editor.minibar(' ( No previous search. )')

@_motion_commands('*')
def do_normal_star(editor, reg=None, part=None, arg=None, count=1):
    editor.registr['/'] = editor.current_buffer[editor.current_buffer.inner_word()].strip()
    editor.actions.normal('n')

@_motion_commands(')')
def do_move_to_next_token(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one token forward.
    """
    with editor.current_buffer as curbuf:
        for _ in range(count):
            curbuf.cursor = curbuf.find_next_token()
