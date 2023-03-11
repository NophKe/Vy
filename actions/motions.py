from vy.actions.helpers import motion_commands
from vy import keys as k
#
# not documented, look at tis old comment
# WORKK IN PROGRESS
#
########    MOTIONS (not valid command operator) #####################
#
# This is something that bothers me... 
#
# In vim, dgd is valid but d<page-down> is not! Why? I *really* want
# d<page-up> to work ! And for now it does not in vim and neither in
# Vy. Why does Vim exhibit such a behaviour?
#
# My guess is some motion are window-related while others buffer or 
# cursor related. And window-related motions are not consistant! By
# this I mean a window redraw may change last shown line on screen 
# as an exemple.
#
# This mean that an action like d<page-down> to work would need that
# relative cursor position on the screen and cursor position on the
# text itself should have properties linking them that may not change
# asynchronously because of a window redraw by example.
# 
# Implementating such a thing is not trivial!
#
# For now in Vy things are a bit more complicated, *true* motions that 
# can be used as operator are buffer dependent and implemented by dict
# Basefile.motion_commands.
# 
# TODO: Change motions commands to be a new kind of actions that may
# be used as motion motion commands and operator pending mode. This
# should unify any kind of motions.
# DONE
# 
# TODO: But for now Basefile.motion_commands contains methods that receive
# a Basefile instance self. Those new kind of actions would receive
# a editor instance and need to resolve editor.current_buffer....
# should be moved to here.
#  
# this means that for now you can't do things like dgd 
# But should this be implemented? I'm not as 100% as with d<page-up>
# But working on it anyway...

@motion_commands('gd')
def goto_definition(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor to the definition of the variable it is on.
    """
    curbuf = editor.current_buffer
    if curbuf.completer_engine is not None:
        lin, col = curbuf.cursor_lin_col
        loc = curbuf.completer_engine.goto(lin+1, col-1)
        if loc:
            lin, col = loc[0].get_definition_start_position()
            curbuf.cursor_lin_col = lin-1, col+1 

@motion_commands(f'i_{k.left} {k.left} h')
def do_normal_h(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one character left.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin, col-count)

@motion_commands(f'i_{k.down} {k.down} j + {k.C_M} {k.C_J} {k.CR}'
                 f'{k.C_J} {k.C_N}')
def do_normal_j(editor, reg=None, part=None, arg=None, count=1):
    """
    Move one line down.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin+count, col)

@motion_commands(f'i_{k.up} {k.up} {k.C_P} k -')
def do_normal_k(editor, reg=None, part=None, arg=None, count=1):
    """
    Move one line up.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin-count, col)

@motion_commands(f'l i_{k.right} {k.space} {k.right}')
def do_normal_l(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one character right.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin, col+count)

@motion_commands('0')
def do_normal_zero(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to beginning of line.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_begining_of_line()

@motion_commands(f'$ {k.end} i_{k.end}')
def do_normal_dollar(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to end of line.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_end_of_line()

@motion_commands('G')
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

@motion_commands('gg')
def do_normal_gg(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to first line first character.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = 0

@motion_commands('_')
def do_normal_underscore(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to the first character of the current line.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_first_non_blank_char_in_line()

@motion_commands(f'B i_{k.C_left} {k.C_left}')
def do_normal_B(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one WORD backwards.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_normal_B()

@motion_commands(f'b i_{k.S_left} {k.S_left}')
def do_normal_b(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one word backwards.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_previous_delim()

@motion_commands(f'W i_{k.C_right} {k.C_right}')
def do_normal_W(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one WORD right.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_next_WORD()

@motion_commands(f'w i_{k.S_right} {k.S_right}')
def do_normal_w(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one word right.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_next_delim()


@motion_commands(f'{k.page_down} i_{k.page_down} {k.C_B}')
def do_page_down(editor, reg=None, part=None, arg=None, count=1):
    """
    First keystrike puts the cursor on last line shown in the current 
    windows. Next keystrokes scrolls the text one page down.
    """
    curbuf = editor.current_buffer
    curwin = editor.current_window
    line_shift = curwin.shift_to_lin
    page_size = curwin.number_of_lin
    lin, col = curbuf.cursor_lin_col
    new_lin = (line_shift + page_size - 1)

    if lin < new_lin:
        curbuf.cursor_lin_col = (new_lin, col)
    else:
        curbuf.cursor_lin_col = (new_lin + page_size, col)

@motion_commands(f'{k.page_up} i_{k.page_up} {k.C_F}')
def do_page_up(editor, reg=None, part=None, arg=None, count=1):
    """
    First keystrike puts the cursor on the first line shown in the current 
    windows. Next keystrokes scrolls the text one page up.
    """
    curbuf = editor.current_buffer
    curwin = editor.current_window
    line_shift = curwin.shift_to_lin
    page_size = curwin.number_of_lin
    lin, col = curbuf.cursor_lin_col

    if lin > line_shift:
        curbuf.cursor_lin_col = (line_shift, col)
    else:
        curbuf.cursor_lin_col = (lin - page_size, col)


@motion_commands("n")
def do_normal_n(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor to next occurrence of last searched text.
    """
    from vy.interface.search_forward import loop
    from vy.keys import C_M
    editor.push_macro(C_M)
    loop(editor)

@motion_commands("N")
def do_normal_N(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor to previous occurrence of last searched text.
    """
    from vy.interface.search_backward import loop
    from vy.keys import C_M
    editor.push_macro(C_M)
    loop(editor)

@motion_commands('*')
def do_normal_star(editor, reg=None, part=None, arg=None, count=1):
    editor.registr['/'] = editor.current_buffer['iw']
    do_normal_n(editor)

del motion_commands
del k
