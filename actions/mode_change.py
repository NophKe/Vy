"""
    *********************************************
    ****    Change From A Mode To Another    ****
    *********************************************

You will find here the common commands to switch from a mode to another.

To switch from a mode to another all an action has to do is to return a
string containing the targeted mode name.  The following shows the most
common ways to swich from a mode to another and may be used as a
reminder but beware that all actions that may take you into an other
mode may not be listed here.

This section only presents «atomic» commands that discard any {count} or
{register} argument.

If you are familiar with other vi-like editor, this should be no suprise. 
Modes correspond to the way keystrokes are interpreted. They do not belong
themselves to any kind of action/command.  

This document is about actions.  To get the different modes
documentation use 'help(Editor.interface)' in python mode.

Modes are much more extensively used in Vy than the classical Vi.  And
Vy has different private sub-modes that the current mode can set.  Modes
are documented in ':help! interface'.
"""

from vy import keys as _k
from vy.editor import _Editor
from vy.actions.helpers import atomic_commands as _atomic_commands


doc_no_edition = """
The next commands change mode but do not make any edition to the content
of any buffer.
"""

@_atomic_commands(f'{_k.escape} i_{_k.escape} v_{_k.escape}' # escape should work in any mode
                  f' {_k.C_C} i_{_k.C_C} v_{_k.C_C}'         # also Ctrl+C
                  f' {_k.F1} i_{_k.F1} v_{_k.F1}'            # also F1 which is next to esc
                  f' ² i_² v_²'                              # also ² which is next to esc
                  f' v_v v_V'                                # v and V from visual mode
                  f' :vi :visual :stopi :stopinsert'         # old vi stuff
                  )
def normal_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Normal» mode.
    """
    return 'normal'

@_atomic_commands(f'{_k.C_V}')
def visual_block(editor, *args, **kwargs):
    """
    Starts «visual block» mode.
    """
    return 'visual_block'

@_atomic_commands('v')
def visual_mode(editor, **kwargs):
    """
    Starts «visual» mode.
    """
    return 'visual'


@_atomic_commands('I')
def do_normal_I(editor: _Editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «insert» mode at beginning of line.
    """
    cb = editor.current_buffer
    cb.cursor = cb.find_begining_of_line()
    return 'insert'

@_atomic_commands(f': {_k.C_W}:')
def command_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Command» mode.
    """
    return 'command'

@_atomic_commands(':python :py')
def python_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Python» mode.
    """
    return 'python'

@_atomic_commands('A')
def do_normal_A(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor on the last character on the current line.
    And starts «Insert» mode.
    """
    editor.actions.normal['$'](editor)
    return 'insert'

@_atomic_commands('?')
def do_search_backward(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «search backward» mode.
    """
    return 'search_backward'

@_atomic_commands(f'i {_k.insert}')
def insert_mode_i(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Insert» mode at cursor position.
    """
    return 'insert'

@_atomic_commands('a')
def insert_mode_a(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Insert» mode one character after cursor position.
    """
    editor.actions.normal['l'](editor)
    return 'insert'

@_atomic_commands('/')
def do_search_forward(editor, reg=None, part=None, arg=None, count=1):
    return 'search_forward'


doc_editing = """
The next commands do modify the content of the current buffer before
switching mode.
"""


@_atomic_commands('o')
def do_normal_o(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor on a new empty line below the current line.
    And starts «Insert» mode.  If the line only contains indentation, it
    is first stripped.
    """
    with editor.current_buffer as curbuf:
        if not curbuf.current_line.strip():
            editor.actions.motion['0'](editor)
            curbuf.current_line = '\n'
        else:    
            editor.actions.motion['$'](editor)
        editor.actions.insert['\n'](editor)
    return 'insert'

@_atomic_commands(f'{_k.backspace} {_k.linux_backpace}')
def insert_mode_backspace(editor: _Editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes the character before the cursor and starts «Insert» mode.
    ---
    NOTE: Not Vim's behaviour.
    """
    editor.current_buffer.backspace()
    return 'insert'

@_atomic_commands('O')
def do_normal_O(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor on a new empty line under the current line.
    And starts «Insert» mode.
    """
    with editor.current_buffer as curbuf:    
        editor.actions.normal['_'](editor)
        editor.actions.insert['\n'](editor)
        editor.actions.normal['k'](editor)
    return 'insert'

@_atomic_commands(f'i_{_k.C_O}')
def do_insert_C_O(editor, **kwargs):
    """
    Performs only one action in normal mode then returns to «insert»
    mode.
    """
    from vy.interface.normal import loop
    loop(editor, False)

@_atomic_commands('vy:paste i_vy:paste')
def paste_from_os_clipboard(editor: _Editor, *args, **kwrags):
    editor.screen.infobar(' ( pasting from OS clipboard )')
    editor.current_buffer.insert(editor.read_stdin())
    return 'normal'

@_atomic_commands('vy:mouse v_vy:mouse i_vy:mouse')
def move_to_click_position(editor: _Editor, *args, **kwrags):
    button = editor.read_stdin()
    click_col = int(editor.read_stdin())
    click_lin = int(editor.read_stdin())
    
    curwin = editor.screen
    new_lin = click_lin + curwin.shift_to_lin - 2
    new_col = max(0, (click_col - 4))

    curbuf = editor.current_buffer
    lin, col = curbuf.cursor_lin_col

    curbuf.cursor_lin_col = new_lin, new_col
    editor.screen.minibar(f' (click {button= }, {click_lin= }, {click_col= })',
                          f' (click {button= }, {new_lin= }, {new_col= })')
