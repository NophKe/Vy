"""
    ***********************************
    ****    The «Full» Commands    ****
    ***********************************

The «full» commands are the commands that require the user to specify
the range of the text that is going to be impacted by the change.

In 'normal mode', these are the commands that await a valid motion or an
operator to work on.  You can also use visual mode to select the range
upon which the action will operate.
"""
from vy.actions.helpers import full_commands as _full_commands

@_full_commands('c v_c')
def change(editor, reg='_', part=None, arg=None, count=1):
    """
    Deletes the text from the cursor position to MOTION argument, or
    inside MOTION if it resolves to as slice of the text.  The discarded
    text is also copied to the {register}.  Then starts 'insert' mode.
    By default, if no register is specified the black hole "_ register
    is used.
    """
    with editor.current_buffer as curbuf:
        stop = part.stop or len(curbuf) - 1
        start = part.start or 0
        if stop - 1 > start and curbuf[stop - 1] == '\n':
            stop = stop - 1
        editor.registr[reg] = curbuf[start:stop]
        del curbuf[start:stop]
        curbuf.cursor = part.start
        return 'insert'

@_full_commands('y v_y')
def yank(editor, reg='+', part=None, arg=None, count=1):
    """
    Yanks (copies) the text from the cursor position to {movement}
    argument, or inside {movement} if it resolves to as slice of the
    text.  By default, if no register is specified the default ""
    register is used.
    """
    text = editor.current_buffer[part]
    editor.registr[reg] = text

@_full_commands('d v_d')
def delete(editor, reg='+', part=None, arg=None, count=1):
    """
    Deletes the text from the cursor position to {movement} argument, or
    inside {movement} if it resolves to as slice of the text.  The
    discarded text is also copied to the {register}. By default, if no
    register is specified the default "" register is used.
    """
    to_be_del = editor.current_buffer[part]
    del editor.current_buffer[part]
    editor.registr[reg] = to_be_del

@_full_commands('gu v_gu')
def lower_case(editor, reg='_', part=None, arg=None, count=1):
    """
    Makes the text lower case from the cursor position to {movement}
    argument, or inside {movement} if it resolves to as slice of the
    text.
    ---
    NOTE: {register} argument is ignored.
    """
    with editor.current_buffer as curbuf:
        curbuf[part] = curbuf[part].lower()
        curbuf.cursor = part.stop

@_full_commands('gU v_gU')
def upper_case(editor, reg='_', part=None, arg=None, count=1):
    """
    Makes the text upper case from the cursor position to {movement}
    argument, or inside {movement} if it resolves to as slice of the
    text.
    ---
    NOTE: {register} argument is ignored.
    """
    with editor.current_buffer as curbuf:
        curbuf[part] = curbuf[part].upper()
        curbuf.cursor = part.stop

@_full_commands('g~ v_g~')
def swap_case(editor, reg='_', part=None, arg=None, count=1):
    """
    Swaps the case of the text from the cursor position to {movement}
    argument, or inside {movement} if it resolves to as slice of the
    text.
    ---
    NOTE: {register} argument is ignored.
    """
    with editor.current_buffer as curbuf:
        curbuf[part] = curbuf[part].swapcase()
        curbuf.cursor = part.stop

del _full_commands
