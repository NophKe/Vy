""" This module contains basic «actions» upon the Vy editor.
An action is a function that accepts an editor as first
argument, and a possibly null, arg string, or slice as
second argument.

As defined in the Vym grammar, some commands require motion
argument, some possibly require a register to work on.

"""

from vy.helpers import (sa_commands, full_commands,
                      with_args_commands, atomic_commands)
from vy import keys as k

########    DEBUGGING ################################################

@atomic_commands('µ')
def print_some(editor, reg=None, part=None, arg=None, count=1):
    """
    This command is used to print variables to debug.
    It looks to a file called "debugging_values" from the user 
    config directory. This file should contain a list of newline
    separated variables from the editor object namespace.
    """
    from vy.global_config import USER_DIR
    from pprint import pformat
    debug_file = USER_DIR / "debugging_values"
    to_print = ''
    for line in debug_file.read_text().splitlines():
        parent = eval(line)
        value = ('\n' + pformat(parent)).replace('\n', '\n\t')
        to_print += f'\x1b[2m{line}\x1b[0m = {value} \n'
    editor.warning(to_print)

@atomic_commands(':pwd :pw :pwd-verbose')
def print_working_directory(editor, reg=None, part=None, arg=None, count=1):
    from pathlib import Path
    editor.screen.minibar(str(Path('.').resolve()))

########    start of motions #########################################


@atomic_commands(f'i_{k.left} {k.left} h')
def do_normal_h(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one character left.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin, col-count)

@atomic_commands(f'i_{k.down} {k.down} j + {k.C_M} {k.C_J} {k.CR}'
                 f'{k.C_J} {k.C_N}')
def do_normal_j(editor, reg=None, part=None, arg=None, count=1):
    """
    Move one line down.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin+count, col)

@atomic_commands(f'i_{k.up} {k.up} {k.C_P} k -')
def do_normal_k(editor, reg=None, part=None, arg=None, count=1):
    """
    Move one line up.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin-count, col)

@atomic_commands(f'l i_{k.right} {k.space} {k.right}')
def do_normal_l(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one character right.
    """
    lin, col = editor.current_buffer.cursor_lin_col
    editor.current_buffer.cursor_lin_col = (lin, col+count)

@atomic_commands('0')
def do_normal_zero(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to end of line.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_begining_of_line()

@atomic_commands(f'$ {k.end} i_{k.end}')
def do_normal_dollar(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to end of line.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_end_of_line()

@atomic_commands('G')
def do_normal_G(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to end of file
    """
    # This does not correspond to the vim behaviour. In vim, G move to the last
    # line on the first collumn, whereas dG deletes till the end of last line.
    # In Vy, G is allways last collumn, last line.
    curbuf = editor.current_buffer
    curbuf.cursor = len(curbuf) - 1

@atomic_commands(f'gg')
def do_normal_gg(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to first line first character.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = 0

@atomic_commands(f'_')
def do_normal_underscore(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor to first line first character.
    """
    curbuf = editor.current_buffer
    curbuf.cursor = curbuf.find_first_non_blank_char_in_line()

@atomic_commands(f'b i_{k.S_left} {k.S_left}')
def do_normal_b(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one word backwards.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_normal_b()

@atomic_commands(f'W i_{k.C_right} {k.C_right}')
def do_normal_W(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one WORD right.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_next_WORD()

@atomic_commands(f'w i_{k.S_right} {k.S_right}')
def do_normal_w(editor, reg=None, part=None, arg=None, count=1):
    """
    Move cursor one word right.
    """
    curbuf = editor.current_buffer
    for _ in range(count):
        curbuf.cursor = curbuf.find_next_delim()

########    end of motions ###########################################

########    start of mode switching ##################################

@atomic_commands(f'i {k.insert}')
def insert_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Insert» mode at cursor position.
    """
    return 'insert'

@atomic_commands(f': {k.C_W}:')
def command_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Command» mode.
    """
    return 'command'

@atomic_commands(':PYTHON :PY')
def python__main__mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Python» mode in the __main__ name space.
    """
    from .interface import python
    from __main__ import __dict__ as main_name_space
    python.name_space = main_name_space
    return 'python'

@atomic_commands(':python :py')
def python_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Python» mode.
    """
    return 'python'
@atomic_commands(f'{k.escape} i_{k.escape} i_{k.C_C} :vi :visual :stopi :stopinsert')
def normal_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «Normal» mode.
    """
    return 'normal'

@atomic_commands('I')
def do_normal_I(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts «insert» mode at beginning of line.
    """
    editor.current_buffer.move_cursor('#.')
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
        curbuf.move_cursor('#.')
        curbuf.insert_newline()
        do_normal_k(editor)
        return 'insert'

@atomic_commands('A')
def do_normal_A(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor on the last character on the current line.
    And starts «Insert» mode.
    """
    editor.current_buffer.move_cursor('$')
    return 'insert'

@sa_commands('J')
def join_lines(editor, reg=None, part=None, arg=None, count=1):
    """
    Joins the {count} next lines together.
    """
    with editor.current_buffer as curbuf:
        for _ in range(count):
            lin, col = curbuf.cursor_lin_col
            if lin + 1 == curbuf.number_of_lin:
                return
            curbuf.current_line = curbuf.current_line.strip() + ' \n'
            curbuf.cursor_lin_col = lin+1, 0
            curbuf.current_line = curbuf.current_line.lstrip(' ')
            curbuf.cursor_lin_col = lin, col
            curbuf.join_line_with_next()

@sa_commands(f'{k.C_W}>')
def increase_window_width_right(editor, reg=None, part=None, arg=None, count=2):
    """
    Increases window width to the right by {count} columns.
    """
    curwin = editor.current_window
    if curwin.parent is curwin: #if it's screen itself
        return
    curwin.parent.move_v_split_right(count)

@sa_commands(f'{k.C_W}<')
def increase_window_width_left(editor, reg=None, part=None, arg=None, count=2):
    """
    Increases window width to the left by {count} columns.
    """
    curwin = editor.current_window
    if curwin.parent is curwin: #if it's screen itself
        return
    curwin.parent.move_v_split_left(count)

@atomic_commands('U u :u :un :undo')
def undo(editor, reg=None, part=None, arg=None, count=1):
    """
    Undo last action in the current buffer.
    Register argument is ignored.
    """
    if arg:
        try:
            count = int(arg)
        except ValueError:
            editor.screen.minibar(f'Wrong count argument: {arg}')
            return
    with editor.current_buffer as curbuf:
        for _ in range(count):
            editor.current_buffer.undo()


#@with_args_commands(f'{k.C_R} :red :redo')
@sa_commands(f'{k.C_R} :red :redo')
def redo(editor, reg=None, part=None, arg=None, count=1):
    """
    Redo last undone action in the current buffer.
    """
    with editor.current_buffer as curbuf:
        for _ in range(count):
            editor.current_buffer.redo()

#@with_args_commands(':nmap :nnoremap')
#def do_nmap(editor, reg=None, part=None, arg=None, count=1):
#    """
#    TODO. Not working anymore (api change)
#    """
#    if not arg or not ' ' in arg:
#        editor.minibar('[SYNTAX]    :nmap [key] [mapping]')
#        return
#    key, value = arg.split(' ', maxsplit=1)
#    editor.current_buffer.stand_alone_commands[key] = lambda ed, reg, part, arg, count: ed.push_macro(value)

@with_args_commands(':reg :registers :di :display')
@atomic_commands(':reg :registers :di :display')
def show_registers(editor, reg=None, part=None, arg=None, count=1):
    """
    Shows the content of registers.
    If an argument is given, only shows the content of this register.
    """
    if arg:
        editor.warning(arg + ': ' + str(editor.registr[arg]))
    else:
        editor.warning(str(editor.registr))
    return 'normal'


@atomic_commands(':files :ls :buffers')
def show_buffers(editor, reg=None, part=None, arg=None, count=1):
    """
    Shows the list of «cached» buffers.
    """
    editor.warning(str(editor.cache))
    return 'normal'


@full_commands('c')
def change(editor, reg='_', part=None, arg=None, count=1):
    """
    Deletes the text from the cursor position to MOTION argument,
    or inside MOTION if it resolves to as slice of the text.
    The discarded text is also copied to the {register}.
    Then starts 'insert' mode.
    By default, if no register is specified the black hole "_ register is used.
    """
    with editor.current_buffer as curbuf:
        stop = part.stop
        start = part.start
        if curbuf[stop - 1] == '\n':
            stop = stop - 1
        editor.registr[reg] = curbuf[start:stop]
        del curbuf[start:stop]
        curbuf.cursor = part.start
        return 'insert'


@full_commands('y')
def yank(editor, reg='"', part=None, arg=None, count=1):
    """
    Yanks (copies) the text from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    By default, if no register is specified the default "" register is used.
    """
    text = editor.current_buffer[part]
    editor.current_buffer.cursor = part.stop
    editor.registr[reg] = text


@full_commands('d')
def delete(editor, reg='"', part=None, arg=None, count=1):
    """
    Deletes the text from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    The discarded text is also copied to the {register}.
    By default, if no register is specified the default "" register is used.
    """
    to_be_del = editor.current_buffer[part]
    del editor.current_buffer[part]
    editor.registr[reg] = to_be_del


@full_commands('gu')
def lower_case(editor, reg='_', part=None, arg=None, count=1):
    """
    Makes the text lower case from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    {register} argument is ignored.
    """
    with editor.current_buffer as curbuf:
        curbuf[part] = curbuf[part].lower()
        curbuf.cursor = part.stop


@full_commands('gU')
def upper_case(editor, reg='_', part=None, arg=None, count=1):
    """
    Makes the text upper case from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    {register} argument is ignored.
    """
    with editor.current_buffer as curbuf:
        curbuf[part] = curbuf[part].upper()
        curbuf.cursor = part.stop


@full_commands('g~')
def swap_case(editor, reg='_', part=None, arg=None, count=1):
    """
    Swaps the case of the text from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    {register} argument is ignored.
    """
    with editor.current_buffer as curbuf:
        curbuf[part] = curbuf[part].swapcase()
        curbuf.cursor = part.stop

########    command mode only ########################################

@with_args_commands(":read :re :r")
def read_file(editor, reg=None, part=None, arg=None, count=1):
    """
    Reads the content of file specified as argument and inserts it at the current
    cursor location.
    TODO: No check is done by this function. May raise exception!
    """
    from pathlib import Path
    if not arg:
        editor.screen.minibar('Commmand needs arg!')
        return
    editor.current_buffer.insert(Path(arg).read_text())


@with_args_commands(":!")
def do_system(editor, reg=None, part=None, arg=None, count=1):
    """
    Execute a system command.
    """
    from os import system
    if not arg:
        editor.screen.minibar('Commmand needs arg!')
    else:
        editor.stop_async_io()
        editor.screen.alternative_screen()
        err = system(arg)
        system(f"read -p 'Command Finished with status: {err}, press enter.")
        editor.start_async_io()

        editor.warning(f'Command Finished with status: {err}')


@with_args_commands(":chdir :chd :cd")
def do_chdir(editor, reg=None, part=None, arg=None, count=1):
    """
    Change current directory
    """
    if not arg:
        editor.screen.minibar('Commmand needs arg!')
        return
    import os
    try:
        os.chdir(arg)
    except FileNotFoundError:
        editor.warning(f'File not found: {arg}')


@with_args_commands(":set :se")
def do_set(editor, reg=None, part=None, arg=None, count=1):
    """
    [SYNTAX]      :set {argument}          >>> set to True
    [SYNTAX]      :set no{argument}        >>> set to False
    [SYNTAX]      :set {argument}!         >>> toggle True/False
    [SYNTAX]      :set {argument} {number} >>> set to integer value
    """

    if not arg:
        editor.warning(do_set.__doc__)
        return

    toggle = object()

    arg = arg.strip().lower()
    if ' ' in arg:
        arg, value = arg.split(' ', maxsplit=1)
        value = int(value)
    elif arg.startswith('no'):
        arg = arg[2:]
        value = False
    elif arg.endswith('!'):
        arg = arg[:-1]
        value = toggle
    else:
        value = True

    try:
        option = getattr(editor.current_buffer, 'set_' + arg)
    except AttributeError:
        editor.screen.minibar(f"Invalid option {arg}")
        return

    if isinstance(option, type(value)):
        setattr(editor.current_buffer, f'set_{arg}', value)
    if value is toggle:
        setattr(editor.current_buffer, f'set_{arg}', not option)


@with_args_commands(":e :edit :ex")
def do_edit(editor, reg=None, part=None, arg=None, count=1):
    """
    Start editing a file in the current window. If the file has allready
    being visited, the file is not read again and the cached version in served
    """
    if arg:
        editor.edit(arg)


@atomic_commands(f"{k.C_W}n {k.C_W}{k.C_N} :new :enew :ene")
def do_enew(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts editing a new unnamed buffer.
    """
    editor.edit(None)


@atomic_commands(':w :write')
@with_args_commands(':w :write')
def do_try_to_save(editor, reg=None, part=None, arg=None, count=1):
    '''anything'''
    if not arg:
        if not editor.current_buffer.unsaved:
            return
        elif editor.current_buffer.path:
            try:
                return editor.current_buffer.save()
            except (IsADirectoryError, FileExistsError, PermissionError) as exc:
                editor.warning(f'{exc.__doc__} quit without saving (:q!) or try to force saving (:w!)')
        else:
            editor.warning('give your file a path (:w some_name) or forget it (:q!).')
    elif arg:
        try:
            return editor.current_buffer.save_as(arg)
        except (IsADirectoryError, FileExistsError, PermissionError) as exc:
            editor.warning(f'{exc.__doc__} quit without saving (:q!) or try to force saving (:w!)')


@atomic_commands(":w! :write!")
@with_args_commands(":w! :write!")
def do_force_to_save(editor, reg=None, part=None, arg=None, count=1):
    """
    TODO
    """
    try:
        if arg:
            editor.current_buffer.save_as(arg,override=True)
        else:
            editor.current_buffer.save(override=True)
    except (IsADirectoryError, FileExistsError, PermissionError) as exc:
        editor.warning(f'{exc.__doc__} aborting...')


@atomic_commands(":wa :wall")
def do_save_all(editor, reg=None, part=None, arg=None, count=1):
    """
    Saves all cached buffers.
    """
    for buf in editor.cache:
        if buf.unsaved:
            buf.save()


@atomic_commands(':n :ne :next')
def do_edit_next_unsaved_buffer(editor, reg=None, part=None, arg=None, count=1):
    """
    Edit next unsaved buffer. If no buffer is unsaved, leaves. 
    """
    next_one = False
    for buf in editor.cache:
        if buf.unsaved:
            next_one = buf
            break
    if next_one:
        editor.edit(next_one.path)
        editor.warning('buffer: ' + repr(editor.current_buffer) + ' save (:w)  or leave! (:q!)')
    else:
        if editor.current_window is editor.screen:
            do_exit_nice(editor, arg)


@atomic_commands(f'{k.C_W}{k.C_H} {k.C_W}{k.C_left} {k.C_W}h')
def do_focus_left_window(editor, reg=None, part=None, arg=None, count=1):
    """
    Focus the window on the left of current focused window.
    """
    editor.current_window.get_left_buffer().set_focus()


@atomic_commands(f'{k.C_W}{k.C_L} {k.C_W}{k.C_right} {k.C_W}l')
def do_focus_right_window(editor, reg=None, part=None, arg=None, count=1):
    """
    Focus the window on the right of current focused window.
    """
    editor.current_window.get_right_buffer().set_focus()


@atomic_commands(f'{k.C_W}o {k.C_W}{k.C_O} :only :on')
def do_keep_only_current_window(editor, reg=None, part=None, arg=None, count=1):
    """
    Closes every windows except the current one.
    """
    while editor.current_window is not editor.screen:
        if editor.current_window is editor.current_window.parent.right_panel:
            editor.current_window.parent.merge_from_right_panel()
        if editor.current_window is editor.current_window.parent.left_panel:
            editor.current_window.parent.merge_from_left_panel()


@atomic_commands(':wq! :x! :xit! :exit!')
def do_save_current_buffer_and_force_leave_window(editor, reg=None, part=None, arg=None, count=1):
    """
    Saves the current buffer and leaves its window. If it is
    the only open window and no unsaved buffer in cache, leaves
    the editor.
    Equivalent to :w <CR> :q <CR>
    """
    do_try_to_save(editor)
    do_force_leave_current_window(editor)


@atomic_commands(':wq :x :xit :exit ZZ')
def do_save_current_buffer_and_try_leave_window(editor, reg=None, part=None, arg=None, count=1):
    """
    Saves the current buffer and leaves its window. If it is
    the only open window and no unsaved buffer in cache, leaves
    the editor.
    Equivalent to :w <CR> :q <CR>
    """
    do_try_to_save(editor)
    do_leave_current_window(editor)


@atomic_commands(':q! :quit! ZQ')
def do_force_leave_current_window(editor, reg=None, part=None, arg=None, count=1):
    """
    Leaves the current window, discarding its buffer, even if it has not been saved.
    """
    curwin = editor.current_window
    del editor.cache[curwin.buff.cache_id]

    if curwin is editor.screen:
        do_exit_nice(editor)
    elif curwin.parent.left_panel is curwin:
        curwin.parent.merge_from_right_panel()
    else:
        curwin.parent.merge_from_left_panel()


@atomic_commands(f':q :quit {k.C_W}{k.C_Q} {k.C_W}q')
def do_leave_current_window(editor, reg=None, part=None, arg=None, count=1):
    """
    Leaves the current window. If this is the only window on screen, tries
    exiting the editor ( unless unsaved buffrs )
    """
    curwin = editor.current_window
    if curwin is editor.screen:
        if curwin.buff.unsaved:
            editor.warning('save this buffer (:w) or force (:q!)')
        else:
            do_exit_nice(editor)
    elif curwin.parent.left_panel is curwin:
        curwin.parent.merge_from_right_panel()
    else:
        curwin.parent.merge_from_left_panel()


@with_args_commands(':vsplit :vs')
@atomic_commands(f'{k.C_W}{k.C_V} {k.C_W}v')
def do_vsplit(editor, reg=None, part=None, arg=None, count=1):
    """
    Splits the current window vertically. If an argument is given, use this
    as new buffer for the new current window.
    """
    editor.current_window.vsplit()
    if arg:
        editor.current_window.change_buffer(editor.cache[arg])


@atomic_commands(":eval")
def do_eval_buffer(editor, reg=None, part=None, arg=None, count=1):
    """
    Evaluates a python buffer.
    Use 'from __main__ import Editor' to make use of it.
    """
    from .interface import python
    from traceback import print_tb
    name_space = {}
    try:
        ret = exec(editor.current_buffer.getvalue(), name_space)
        #editor.warning(f'eval returned {ret}')
    except Exception as Err:
        print_tb(Err.__traceback__)
        editor.warning(f'buggy progrm: {Err}')
        return 'normal'
    python.name_space = name_space
    return python.loop(editor)


@atomic_commands(":quitall :quita :qall :qa")
def do_exit_nice(editor, reg=None, part=None, arg=None, count=1):
    """
    Exits Vy except if there are unsaved buffers. In this case switch current window
    to next unsaved buffer.
    """
    if not any([buffer.unsaved for buffer in editor.cache]):
        do_exit_hard(editor)
    else:
        do_edit_next_unsaved_buffer(editor)


@atomic_commands(':wqa! :wqall! :xa! :xall!')
def do_save_all_and_leave_all(editor, arg=None, reg=None, part=None, count=1):
    """
    Saves all unsaved buffers, no matter if this succeeds, closes the editor.
    """
    do_save_all(editor)
    do_exit_hard(editor)


@atomic_commands(':wqa :wqall :xa :xall')
def do_save_all_and_try_leave_all(editor, arg=None, reg=None, part=None, count=1):
    """
    Saves all unsaved buffers, and if this succeeds, closes the editor.
    """
    do_save_all(editor)
    do_exit_nice(editor)


@atomic_commands(":quitall! :quita! :qall! :qa! ZZ")
def do_exit_hard(editor, reg=None, part=None, arg=None, count=1):
    """
    Exits Vy immediatly without checking for any unsaved buffer.
    """
    import sys
    sys.exit(0)


@atomic_commands("zz")
def do_zz(editor, reg=None, part=None, arg=None, count=1):
    """
    Recenters the screen to make cursor line the central line.
    Warning: not to confund with ZZ. 
    """
    curwin = editor.current_window
    middle = (curwin.number_of_lin + 1) / 2
    lin, _ = curwin.buff.cursor_lin_col
    new_pos = int(lin - middle)
    if new_pos <= 0:
        curwin.shift_to_lin = 0
    elif new_pos > curwin.buff.number_of_lin:
        curwin.shift_to_lin = curwin.number_of_lin
    else:
        curwin.shift_to_lin = new_pos


@atomic_commands("z-")
def do_z__MINUS__(editor, reg=None, part=None, arg=None, count=1):
    """
    Recenters the screen to make cursor line the bottom line.
    (like zb does) but cursor is placed on the first non blank
    caracter of the line.
    """
    curbuf = editor.current_buffer
    do_zb(editor)
    curbuf.move_cursor('0')
    curbuf.move_cursor('_')

@atomic_commands("z.")
def do_z__DOT__(editor, reg=None, part=None, arg=None, count=1):
    """
    Recenters the screen to make cursor line the middle line.
    (like zz does) but cursor is placed on the first non blank
    caracter of the line.
    """
    curbuf = editor.current_buffer
    do_zz(editor)
    curbuf.move_cursor('0')
    curbuf.move_cursor('_')


@atomic_commands(f'{k.C_D}')
def scroll_one_screen_down(editor, reg=None, part=None, arg=None, count=1):
    """
    Scrolls one line down. Ajust cursor position so that it is keeps on
    the top line, if it were to escape the current window.
    """
    curwin = editor.current_window
    curbuf = editor.current_buffer
    curwin.shift_to_lin = max(curwin.number_of_lin, ( curwin.shift_to_lin
                                                    + curwin.number_of_lin))
    current_line_idx = curbuf.current_line_idx
    if curwin.shift_to_lin > current_line_idx:
        curbuf.move_cursor(f'#{curwin.shift_to_lin}')

@atomic_commands(f'{k.C_E}')
def scroll_one_line_down(editor, reg=None, part=None, arg=None, count=1):
    """
    Scrolls one line down. Ajust cursor position so that it is keeps on
    the top line, if it were to escape the current window.
    """
    curwin = editor.current_window
    curbuf = editor.current_buffer
    if curwin.shift_to_lin < curbuf.number_of_lin:
        curwin.shift_to_lin += 1
    current_line_idx, _ = curbuf.cursor_lin_col
    if curwin.shift_to_lin > current_line_idx:
        curbuf.move_cursor('j')


@atomic_commands(f"z{k.C_M}")
def do_z__CR__(editor, reg=None, part=None, arg=None, count=1):
    """
    Recenters the screen to make cursor line the top line.
    (like zt does) but cursor is placed on the first non blank
    caracter of the line.
    """
    curbuf = editor.current_buffer
    do_zt(editor)
    curbuf.move_cursor('0')
    curbuf.move_cursor('_')


@atomic_commands("zt")
def do_zt(editor, reg=None, part=None, arg=None, count=1):
    """
    Recenters the screen to make cursor line the top line.
    """
    curwin = editor.current_window
    lin, _ = curwin.buff.cursor_lin_col
    new_pos = lin
    if new_pos <= 0:
        curwin.shift_to_lin = 0
    elif new_pos > curwin.buff.number_of_lin:
        curwin.shift_to_lin = curwin.number_of_lin
    else:
        curwin.shift_to_lin = new_pos


@atomic_commands("zb")
def do_zb(editor, reg=None, part=None, arg=None, count=1):
    """
    Recenters the screen to make cursor line the bottom line.
    """
    curwin = editor.current_window
    lin, _ = curwin.buff.cursor_lin_col
    new_pos = lin - curwin.number_of_lin
    if new_pos <= 0:
        curwin.shift_to_lin = 0
    elif new_pos > curwin.buff.number_of_lin:
        curwin.shift_to_lin = curwin.number_of_lin
    else:
        curwin.shift_to_lin = new_pos


@atomic_commands(f'{k.page_down} i_{k.page_down} {k.C_B}')
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

@atomic_commands(f'{k.page_up} i_{k.page_up} {k.C_F}')
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


@atomic_commands("n")
def do_normal_n(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor to next occurrence of last searched text.
    """
    # This code is sadly a duplicate of vy.interface.search_*
    # TODO find a place to merge it all
    needle = editor.registr['/']

    if not needle:
        editor.screen.minibar('No previous search!')
        return
    curbuf = editor.current_buffer

    offset = curbuf._string.find(needle, curbuf.cursor+1)
    if offset == -1:
        editor.screen.minibar('String not found: back to the top.')
        offset = curbuf._string.find(needle)
        if offset == -1:
            editor.screen.minibar('String not found!')
            return
        curbuf.cursor = offset
    else:
        curbuf.cursor = offset + 1
        return


@atomic_commands("N")
def do_normal_N(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the cursor to previous occurrence of last searched text.
    """
    needle = editor.registr['/']

    if not needle:
        editor.screen.minibar('No previous search!')
        return
    curbuf = editor.current_buffer

    offset = curbuf._string.rfind(needle, 0, curbuf.cursor)
    if offset == -1:
        editor.screen.minibar('String not found: back to the bottom.')
        offset = curbuf._string.rfind(needle)
        if offset == -1:
            editor.screen.minibar('String not found!')
            return
        curbuf.cursor = offset
    else:
        curbuf.cursor = offset + 1
        return


@atomic_commands("r")
def do_r(editor, reg=None, part=None, arg=None, count=1):
    """
    Replace the character under the cursor by next keystrike.
    """
    editor.current_buffer['cursor'] = editor.read_stdin()


@atomic_commands(f'i_{k.backspace} X')
def do_backspace(editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes the character on the left of the cursor, joining current line
    with the previous one if on the first position of the line.
    Does nothing if on the first position of the buffer.
    """
    editor.current_buffer.backspace()


@sa_commands('D')
def do_normal_D(editor, reg='"', part=None, arg=None, count=1):
    """
    Deletes text from the cursor to the end of line. Text is copied to the
    specified register. If no register is specified, use default " register.
    """
    with editor.current_buffer as curbuf:
        lin, col = curbuf.cursor_lin_col
        editor.registr[reg] = curbuf.current_line[:col]
        curbuf.current_line = curbuf.current_line[:col] + '\n' 
        return 'normal'


@atomic_commands(f'i_{k.suppr} x')
def do_suppr(editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes the character under the cursor, joining current line with the
    next one if on the last position of the line.
    Does nothing if on the last position of the buffer.
    """
    editor.current_buffer.suppr()


@sa_commands("~")
def do_normal_tilde(editor, reg=None, part=None, arg=None, count=1):
    """
    Makes the character under the cursor upper case, and moves the cursor
    one character right unless if on the last position of the line.
    Optionnal "{register} argument is ignored.
    """
    with editor.current_buffer as curbuf:
        curbuf[curbuf.cursor] = curbuf[curbuf.cursor].upper()
        curbuf.move_cursor('l')


@sa_commands("C")
def do_normal_C(editor, reg='"', part=None, arg=None, count=1):
    """
    Yanks the text from the cursor to the register, the delete it and starts
    'insert' mode.
    By default, if no register is specified the default "" register is used.
    Optionnal {count} argument is ignored.
    """
    with editor.current_buffer as curbuf:
        editor.registr[reg] = curbuf['cursor:$']
        del curbuf['cursor:$']
        return 'insert'


# TODO Add k.F1 and i_k.F1( but set value in keys.py first ) 
@with_args_commands(':help :h')
def do_help(editor, reg=None, part=None, arg=':help', count=1):
    """
    [SYNTAX] :help TOPIC

    For help about a command mode command prepend: :
        :help :help

    For help about a insert mode command prepend: i_
        :help i_^R

    For help about a visual mode command prepend: v_
        :help v_O

    For help about a normal mode command just type it!
        :help ~

    For help on using help, press h now!

    TODO: To enter a "special key" prepend [CTRL+V].
    """
    try:
        if arg.startswith(':'):
            arg = editor.actions.command[arg[1:]]
        elif arg.startswith('i_'):
            arg = editor.actions.insert[arg[2:]]
        elif arg.startswith('v_'):
            arg = editor.actions.visual[arg[2:]]
        else:
            arg = editor.actions.normal[arg]
    except KeyError:
        editor.warning(f'{arg} not found in help.')
        return 'normal'

    editor.stop_async_io()
    help(arg)
    editor.start_async_io()
    return 'normal'


@sa_commands("p")
def do_paste(editor, reg='"', part=None, arg=None, count=1):
    """
    Paste the text from specified register after the cursor.
    By default, if no register is specified the default "" register is used.
    """
    #from vy.editor import BP; BP()
    editor.current_buffer.insert(editor.registr[reg])


@atomic_commands('i_\t')
def do_insert_expandtabs(editor, reg=None, part=None, arg=None, count=1):
    """
    Inserts the necessery number of spaces to reach next level of indentation

    """
    with editor.current_buffer as curbuf:
        curbuf.insert('\t')
        orig = curbuf['0:$']   # TODO use current_line property
        after = orig.expandtabs(tabsize=curbuf.set_tabsize)
        curbuf['0:$'] = after
        curbuf.cursor += len(after) - len(orig)


@atomic_commands("gf")
def do_normal_gf(editor, reg=None, part=None, arg=None, count=1):
    """
    Interpret the word the cursor is on as a file name, and try to open it.
    If the file cannot be found in the folder that contains the current buffer,
    Vym will try adding it '.py' suffix. And if the file starts with one or two
    dots (as in a python package), Vym will search in the parents directories.
    """
    from pathlib import Path
    filename = editor.current_buffer['iw']
    guess1 = editor.current_buffer.path.with_name(filename)
    guess2 = editor.current_buffer.path.with_name(filename + '.py')
    guess3 = editor.current_buffer.path.parent / (filename.removeprefix('.') + '.py')
    guess4 = editor.current_buffer.path.parent.parent / (filename.removeprefix('..') + '.py')

    for guess in [Path(filename), guess1, guess2, guess3, guess4]:
        if guess.exists():
            editor.edit(guess)
            return 'normal'
    editor.screen.minibar(f'file {filename!r} not found.')
    return 'normal'


@atomic_commands(':HELP')
def dump_help(editor, reg=None, arg=None, part=None, count=1):
    """
    Dumps help text of all recognized commands of the standard modes to a 
    new unnamed buffer.
    """
    editor.edit(None)
    curbuf = editor.current_buffer
    #editor.stop_async_io()
    #breakpoint()
    #with curbuf:
    for k, v in globals().items():
        if not k.startswith('_'):
            curbuf.insert(v.__doc__ + '\n')
    curbuf.cursor = 0
        #curbuf.string


del sa_commands, full_commands, atomic_commands
del with_args_commands, k
