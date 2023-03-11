from vy import keys as k
from vy.actions.helpers import atomic_commands

@atomic_commands(f'{k.escape} ² i_² v_² i_{k.escape} v_{k.escape} i_{k.C_C} v_{k.C_C}'
                  ' :vi :visual :stopi :stopinsert')
def normal_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Normal» mode.
    """
    return 'normal'

@atomic_commands('v')
def visual_mode(editor, **kwargs):
    return 'visual'

@atomic_commands(f'i_{k.C_O}')
def do_insert_C_O(editor, **kwargs):
    """
    Performs only one action in normal mode then returns to «insert»
    mode.
    """
    from vy.interface.normal import loop
    loop(editor, False)

@atomic_commands('I')
def do_normal_I(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «insert» mode at beginning of line.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = lin, 0
    return 'insert'

@atomic_commands('o')
def do_normal_o(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor on a new empty line below the current line.
    And starts «Insert» mode.
    """
    with editor.current_buffer as curbuf:
        curbuf.move_cursor('$')
        curbuf.insert_newline()
        return 'insert'

@atomic_commands('?')
def do_search_backward(editor, reg=None, part=None, arg=None, count=1):
    return 'search_backward'

@atomic_commands(f'i {k.insert}')
def insert_mode_i(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Insert» mode at cursor position.
    """
    return 'insert'

@atomic_commands('a')
def insert_mode_a(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Insert» mode one character after cursor position.
    """
    editor.current_buffer.move_cursor('l')
    return 'insert'

@atomic_commands(f'{k.backspace} {k.linux_backpace}')
def insert_mode_backspace(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Insert» mode one character after cursor position.
    """
    editor.current_buffer.backspace()
    return 'insert'

@atomic_commands(f': {k.C_W}:')
def command_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Command» mode.
    """
    return 'command'

@atomic_commands(':python :py')
def python_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Python» mode.
    """
    return 'python'

@atomic_commands('Q')
def ex_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Fed up of hitting the 'Q' key in vim? Try the new EX mode !!
    Use the minibar as a python repl. The Editor can be accessed
    by the 'Editor' variable.
    """
    return 'ex'

@atomic_commands('/')
def do_search_forward(editor, reg=None, part=None, arg=None, count=1):
    return 'search_forward'

@atomic_commands('O')
def do_normal_O(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor on a new empty line under the current line.
    And starts «Insert» mode.
    """
    with editor.current_buffer as curbuf:
        lin, col = curbuf.cursor_lin_col
        curbuf.cursor_lin_col = lin, 0
        curbuf.insert_newline()
        curbuf.cursor_lin_col = lin, 0
        return 'insert'

@atomic_commands('A')
def do_normal_A(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor on the last character on the current line.
    And starts «Insert» mode.
    """
    editor.current_buffer.move_cursor('$')
    return 'insert'

del atomic_commands, k
