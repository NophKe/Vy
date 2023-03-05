""" 
This module contains basic «actions» upon the Vy editor.
An action is a function that accepts an editor as first
argument, and a possibly null, arg string, or slice as
second argument.

As defined in the Vym grammar, some commands require motion
argument, some possibly require a register to work on.

"""
from vy.actions.helpers import (sa_commands,
                                with_args_commands,
                                atomic_commands)

from vy.actions.mode_change import *
from vy.actions.motions import *
from vy.actions.commands import *
from vy import keys as k

@sa_commands('M')
@atomic_commands('µ')
def print_some(editor, reg=None, part=None, arg=None, count=1):
    """
    This command is used to print variables to debug.  It looks to a file
    called "debugging_values" from the user config directory. This file should
    contain a list of newline separated variables from the editor object
    namespace.
    """
    from vy.global_config import USER_DIR
    from pprint import pformat
    vy = editor # shorter to type
    debug_file = USER_DIR / "debugging_values"
    to_print = ''
    for line in debug_file.read_text().splitlines():
        parent = eval(line)
        value = ('\n' + pformat(parent)).replace('\n', '\n\t')
        to_print += f'\x1b[2m{line}\x1b[0m = {value} \n'
    editor.warning(to_print)

@atomic_commands(f'i_{k.C_A}')
def insert_last_inserted_text(editor, **kwargs):
    """
    Re-insert last inserted text at cursor position.
    """
    editor.current_buffer.insert(editor.registr['.'])
    
@with_args_commands(':%s')
def replace_all(editor, reg=None, part=None, arg=None, count=1):
    if not arg or not ' ' in arg:
        editor.warning('bad syntax')
        return
    with editor.current_buffer as curbuf:
        old, new = arg.split(' ', maxsplit=1)
        for idx, line in enumerate(curbuf.splited_lines):
            curbuf._splited_lines[idx] = line.replace(old, new)
        curbuf._lines_offsets.clear()
        curbuf._string = ''.join(curbuf._splited_lines)
        curbuf._lengh = len(curbuf._string)
        

@atomic_commands(f'{k.C_A} i_{k.C_A}')
def increment(editor, reg=None, part=None, arg=None, count=1):
    # this is buggy because iw is buggy         # bug
    cur_word = editor.current_buffer['iw']      .replace('\n','')
#    editor.warning(repr(cur_word))
    if cur_word.isnumeric():
        editor.current_buffer['iw'] = str(int(cur_word)+1)

@with_args_commands(':debug')
def debug_tool(editor, reg=None, part=None, arg='reload', count=1):
    from vy import debug_tools
    func = getattr(debug_tools, arg, None)
    if func is None:
        editor.screen.minibar('debug func not found', f'{dir(debug_tools) = }')
    else:
        func(editor)

@sa_commands('# :comment')
def comment_current_line(editor, reg=None, part=None, arg=None, count=1):
    """
    Comment the current line.
    """
    if any((token := editor.current_buffer.set_comment_string)):
        with editor.current_buffer as curbuf:
            before, after = token
            for index in range(count):
                curlin = curbuf.current_line
                if not curlin.lstrip().startswith(before):
                    curbuf.current_line = before + curlin[:-1] + after + '\n'
                if index != count - 1:
                    curbuf.move_cursor('j')

@sa_commands('>> :indent')
def indent_current_line(editor, reg=None, part=None, arg=None, count=1):
    """
    Indent the current line.
    """
    with editor.current_buffer as curbuf:
        last_line = curbuf.number_of_lin
        last_target = curbuf.current_line_idx + count
        max_line = min(last_line, last_target)
        indent = curbuf.set_tabsize * ' '
        curbuf.move_cursor('_')
        for idx in range(curbuf.current_line_idx, max_line):
            cur_lin = curbuf.current_line
            curbuf.current_line = indent + cur_lin
            if idx != max_line - 1:
                curbuf.move_cursor('j')

@sa_commands('<< :dedent')
def dedent_current_line(editor, reg=None, part=None, arg=None, count=1):
    """
    Dedent the current line.
    """
    with editor.current_buffer as cur_buf:
        indent = cur_buf.set_tabsize * ' '
        last_line = cur_buf.number_of_lin
        last_target = cur_buf.current_line_idx + count
        max_line = min(last_line, last_target)
        indent = cur_buf.set_tabsize * ' '
        cur_buf.move_cursor('_')
        for idx in range(cur_buf.current_line_idx, max_line):
            cur_lin = cur_buf.current_line
            if cur_lin.startswith(indent):
                cur_buf.current_line = cur_lin.removeprefix(indent)
            elif cur_lin.startswith('\t'):
                cur_buf.current_line = cur_lin.removeprefix('\t')
            elif cur_lin.startswith(' '):
                cur_buf.current_line = cur_lin.lstrip()
            if idx != max_line - 1:
                cur_buf.move_cursor('j')
        cur_buf.move_cursor('_')

@atomic_commands(':source%')
def execute_python_file(editor, reg=None, part=None, arg=None, count=1):
    from __main__ import __dict__ as main_dict
    exec(editor.current_buffer.string, main_dict)


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
            curbuf.current_line = curbuf.current_line.rstrip() + ' \n'
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

@sa_commands('U u :u :un :undo')
def undo(editor, reg=None, part=None, arg=None, count=1):
    """
    Undo last action in the current buffer.
    Register argument is ignored.
    ---
    NOTE:
    In Vy there is no difference between 'U' and 'u'
    ---
    """
    if arg:
        try:
            count = int(arg)
        except ValueError:
            editor.screen.minibar(f'Wrong count argument: {arg}')
            return
    with editor.current_buffer as curbuf:
        for _ in range(count):
            curbuf.undo()

@sa_commands(f'{k.C_R} :red :redo')
def redo(editor, reg=None, part=None, arg=None, count=1):
    """
    Redo last undone action in the current buffer.
    """
    with editor.current_buffer as curbuf:
        for _ in range(count):
            curbuf.redo()

@with_args_commands(':nmap :nnoremap')
def do_nmap(editor, reg=None, part=None, arg=None, count=1):
    """
    WARNING RECURSIVE MAPPING !!!!
    """
    if not arg or not ' ' in arg:
        editor.minibar('[SYNTAX]    :nmap [key] [mapping]')
        return
    key, value = arg.split(' ', maxsplit=1)
    func = lambda ed, *args, **kwargs: ed.push_macro(value)
    func.motion = False
    func.atomic = True
    editor.actions.normal[key] = func

@atomic_commands(':pwd :pw :pwd-verbose')
def print_working_directory(editor, reg=None, part=None, arg=None, count=1):
    from pathlib import Path
    editor.screen.minibar(str(Path('.').resolve()))

#@with_args_commands(':reg :registers :di :display')
@atomic_commands(':reg :registers :di :display')
def show_registers(editor, reg=None, part=None, arg=None, count=1):
    """
    Shows the content of registers.
    If an argument is given, only shows the content of this register.
    """
    if arg:
        if arg in editor.registr:
            editor.warning(arg + ': ' + str(editor.registr[arg]))
        else:
            editor.warning(f'{arg} is not a valid register')
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

@atomic_commands("r")
def do_r(editor, reg=None, part=None, arg=None, count=1):
    """
    Replace the character under the cursor by next keystrike.
    """
    editor.current_buffer['cursor'] = editor.read_stdin()

########    command mode only ########################################

@with_args_commands(":read :re :r")
def read_file(editor, reg=None, part=None, arg=None, count=1):
    """
    Reads the content of file specified as argument and inserts it at the
    current cursor location.
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
    from subprocess import run, CalledProcessError
    if not arg:
        editor.warning('Commmand needs arg!')
    else:
        completed = run(arg, capture_output=True, shell=True, text=True)
        retval = completed.returncode
        output = completed.stdout + completed.stderr
        editor.warning( f'{output}\nCommand Finished with status: {retval or "OK"}')
    
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
    except NotADirectoryError:
        editor.warning(f'Not a directory: {arg}')

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
    Saves the current buffer and leaves its window. If it is the only open
    window and no unsaved buffer in cache, leaves the editor.
    Equivalent to :w <CR> :q <CR>
    """
    do_try_to_save(editor)
    do_force_leave_current_window(editor)


@atomic_commands(':wq :x :xit :exit ZZ ')
def do_save_current_buffer_and_try_leave_window(editor, reg=None, part=None, arg=None, count=1):
    """
    Saves the current buffer and leaves its window. If it is the only open
    window and no unsaved buffer in cache, leaves the editor.
    Equivalent to :w <CR> :q <CR>
    """
    do_try_to_save(editor)
    do_leave_current_window(editor)


@atomic_commands(f':q! :quit! ZQ {k.C_C}{k.C_D}')
def do_force_leave_current_window(editor, reg=None, part=None, arg=None, count=1):
    """
    Leaves the current window, discarding its buffer, even if it has not been
    saved.
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


@atomic_commands(f':vsplit :vs {k.C_W}{k.C_V} {k.C_W}v')
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
    from vy.interface import python
    local_dict = {}
    editor.stop_async_io()
    exec(editor.current_buffer.string, {}, local_dict)
    return python.loop(editor, source=local_dict)


@atomic_commands(":quitall :quita :qall :qa")
def do_exit_nice(editor, reg=None, part=None, arg=None, count=1):
    """
    Exits Vy except if there are unsaved buffers. In this case switch 
    current window to next unsaved buffer.
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
    middle = (curwin.number_of_lin + 1) // 2
    lin, _ = curwin.buff.cursor_lin_col
    new_pos = lin - middle
    if new_pos <= 0:
        curwin.shift_to_lin = 0
    elif new_pos > curwin.buff.number_of_lin:
        curwin.shift_to_lin = curwin.number_of_lin
    else:
        curwin.shift_to_lin = new_pos


@atomic_commands("z-")
def do_z__MINUS__(editor, reg=None, part=None, arg=None, count=1):
    """
    Recenters the screen to make cursor line the bottom line.  (like zb does)
    but cursor is placed on the first non blank caracter of the line.
    """
    curbuf = editor.current_buffer
    do_zb(editor)
    curbuf.move_cursor('0')
    curbuf.move_cursor('_')

@atomic_commands("z.")
def do_z__DOT__(editor, reg=None, part=None, arg=None, count=1):
    """
    Recenters the screen to make cursor line the middle line.  (like zz does)
    but cursor is placed on the first non blank caracter of the line.
    """
    curbuf = editor.current_buffer
    do_zz(editor)
    curbuf.move_cursor('0')
    curbuf.move_cursor('_')


@atomic_commands(f'{k.C_D}')
def scroll_one_screen_down(editor, reg=None, part=None, arg=None, count=1):
    """
    Scrolls one line down. Ajust cursor position so that it is keeps on the
    top line, if it were to escape the current window.
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
    Recenters the screen to make cursor line the top line.  (like zt does) but
    cursor is placed on the first non blank caracter of the line.
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

@atomic_commands(f'i_{k.backspace} i_{k.linux_backpace} X')
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
        editor.registr[reg] = curbuf.current_line[col:]
        curbuf.current_line = curbuf.current_line[:col-1] + '\n' 
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
def do_paste_after(editor, reg='"', part=None, arg=None, count=1):
    """
    Paste the text from specified register after the cursor.
    By default, if no register is specified the default "" register is used.
    ---
    NOTE:
    The of 'p' in vy is to paste *after* the cursor. When 'P'
    (capital) pastes *before* the cursor. This is the opposite of vim's
    defaults.
    ---
    """
    to_insert = editor.registr[reg]
    if to_insert:
        with editor.current_buffer as curbuf:
            if '\n' in to_insert:
                curbuf.move_cursor('$')
                if not to_insert.startswith('\n'):
                    curbuf.insert_newline()
            editor.current_buffer.insert(to_insert.removesuffix('\n'))

@sa_commands("P")
def do_paste_before(editor, reg='"', part=None, arg=None, count=1):
    """
    Paste the text from specified register before the cursor.
    By default, if no register is specified the default "" register is used.
    ---
    NOTE:
    The behaviour of 'p' in vy is to paste *after* the cursor. When 'P'
    (capital) pastes *before* the cursor. This is the opposite of vim's
    defaults.
    ---
    """
    to_insert = editor.registr[reg]
    if to_insert:
        with editor.current_buffer as curbuf:
            if '\n' in to_insert:
                curbuf.cursor = curbuf.find_begining_of_line()
            if curbuf.cursor and curbuf[curbuf.cursor-1] != '\n':
                curbuf.cursor -= 1
            curbuf.insert(editor.registr[reg])

@atomic_commands('i_\n i_\r i_{k.C_J} i_{k.C_M}')
def do_insert_newline(editor, reg=None, part=None, arg=None, count=1):
    """
    Inserts the a newline.

    """
    editor.current_buffer.insert_newline()

@atomic_commands('i_\t')
def do_insert_expandtabs_or_start_completion(editor, reg=None, part=None, arg=None, count=1):
    """
    Inserts the necessery number of spaces to reach next level of indentation

    """
    completer = editor.screen.minibar_completer
    curbuf = editor.current_buffer
    if not completer:
        lin, col = curbuf.cursor_lin_col
        curline = curbuf.current_line
        before = curline[:col-1]
        if before and (not before.isspace() and not before.endswith(' ')): # and (before[col-1] not in '\t\n '):
            completer.set_callbacks(lambda: curbuf.get_completions(), lambda: curbuf.check_completions())
            if completer:
                return 'completion'
            else:
                completer.give_up()

    with editor.current_buffer as curbuf:
        curbuf.insert('\t')
        if curbuf.set_expandtabs:
            orig = curbuf['0:$']  # TODO use current_line property
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
    filename = editor.current_buffer['iw'].lstrip().strip()
    if filename.startswith('/') or filename[1:3] == ':\\':
        if Path(filename).exists():
            return editor.edit(filename)
    cur_buf = editor.current_buffer
    for guess in [ cur_buf.path.parent / filename,
        cur_buf.path.parent / (filename + '.py'),
        cur_buf.path.parent / (filename.removeprefix('.').replace('.','/') + '.py'),
        cur_buf.path.parent.parent.parent / (filename.removeprefix('..').replace('.','/') + '.py'),
        cur_buf.path.parent / (filename.removeprefix('.').replace('.','/') + '.py'),
        ]:
#        editor.warning(str(guess))
        if guess.exists():
            editor.edit(guess)
        editor.screen.minibar(f'file {filename!r} not found.')

########    DEBUGGING ################################################

@atomic_commands(':HELP')
def dump_help(editor, reg=None, arg=None, part=None, count=1):
    """
    Dumps help text of all recognized commands of the standard modes to a 
    new unnamed buffer.
    """
    editor.edit(None)
    with editor.current_buffer as curbuf:
        for k, v in globals().items():
            if not k.startswith('_'):
                curbuf.insert(v.__doc__ + '\n')
        curbuf.cursor = 0
        curbuf.string


del sa_commands, atomic_commands, with_args_commands, k
