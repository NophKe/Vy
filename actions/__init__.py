""" 
    ******************************
    ****    Welcome To Vy.    ****
    ******************************

This document lists all of the Vy commands that are natively included.

Most of these commands are accessible by different key mappings
depending on the currently running mode, and this documentation tries to
minimize duplication by giving you all the different aliases of a
command.

NOTE:
-----
  If you are reading from the sources, the vy.actions module contains
  all the basic «actions» upon the Vy editor and get to produce the
  final Vy documentation which is accessible through the  ':help'
  command.  A complete view of the documentation can be produced with
  the  ':help! actions'  command.
  
  Vy's code is intended to be readable, and because of the use of
  docstring for the high level documentation, most of the implementation
  details will remain inside comments.  Remember that you can use
  ':python' anytime or use 'Q' in normal mode and use the regular python
  help() function to access documentation of the objects that are not
  directly available by the classical vim-like help system.
  
  If you are a completely new to using Vi-like text editor, you are
  recommended to execute 'vy --tutor' at least once.
  If you don't know yet what 'python mode' is just 'vy --tutor' ;-)

The fundamental concept of the «Vy grammar» is the action.  There are
different types of actions and each may require specific arguments to
operate on.  Actions are a generalisation of the classical Vi concept of
a command.  But when Vi has regularities in the way each command work,
each has its own subtleties and quircks.  In Vy, each kind of action
have a strict grammar and behaviour may be predicted.

 - Atomic Commands:
        Those are the command that don't need you to supply any register,
        count, or motion to be executed.  Good example is the ':'
        command in normal mode.  This will take you to command mode no
        matter what you typed before and no count or selected register
        can apply to that command.  If any is given this will be ignored.

 - Motion Commands:
        Those actions can take a count to indicate a number of
        repetition.  If given a register this will be ignored.  Those
        actions can also be used as an operators after a «full» command.

 - Full Commands:
        These actions are the ones that require you to specify an
        operator.  You can think about the 'd' command in normal
        mode that does nothing until you choose a range to operate on.

 - Stand-alone Commands:
        These are the actions that can be repeated.  They then accept an
        optional count and an optionnal register even if some actions
        may just ignore the given register.
        Line-wise commands (like normal mode 'J') and character-wise
        commands (like normal mode '~') fall into that category.

 - Operators:
        Operators are all the valid actions that can be used after a
        full command, that are not motions, like 'iw'.  Those are like
        motions but they cannot be used with a count nor directly like a
        motion.

 - With Args Commands:
        These are the command mode commands that accept a string
        argument, like ':w' that may accept a valid filename, or have a
        default behaviour when used without.  These actions have an
        additionnal '.completer' attribute that determinates the kind of
        auto-completion that needs to be triggered.

NOTE:
-----
  This strict categorisation of action type may seem to be a constraint
  but this allows to write an action and get it to perform differently
  in different circomstances.
  
  In Vy implementing an action like normal 'd' command (that belong to
  full commands) will make you get normal 'dd', '{visual}d', 'd{count}d'
  an others, automaticaly.  This is only possible because no action is ever
  responsible for parsing user input.
 
Most of the actions are accesible by different key mappings depending on
which mode the editor is currently running.  And the ways to pass
arguments to the actions depend on the current mode.  See a perticular
mode documentation for more about argument parsing.  The next sections of 
this document will briefly introduce the different modes.

During Vy initialisation phase, actions '.__doc__' atribute  will be
updated to reflect each way any action may be used depending on the
mode, as well as the different aliases that reference the same action.
This will be presented like:

    This command is part of normal mode «full» commands.
    
    [SYNTAX]      ["{register}] [{count}] P
    aliases: P
    -------------------------------------------------------------------
    Pastes the content of {register} at cursor position.

The first line indicates the kind of actions and the mode for which the
aliases will be valid.  The «SYNTAX» line gives you a quick overview of
the syntax for that kind of actions in this specific mode.  Around
squared brackets are optionnal arguments.  Any character must be typed
"as is" except the action arguments that are surrounded with curly
brackets.

Allthough implemented in different ways, all actions share the fact that
they are regular python functions that accept an editor instance as
first argument.  Only the remaining part of their signature may change.

This document firsts sections are about Vy specific commands.  Next
follow the most widely used commands of the text editor.  When Vy
behaviour differs from what you may be used to in Vim, this will be
stated as clearly as possible.  Lasts sections will be about the help
system and the internals of the different commands implementations.
"""
#
#  When the documentation get generated, Vy will aggregate:
#    - The module's docstring
#    - all non underscore-prefixed callables'  docstrings
#    - all instance of str with name starting with 'doc_'
#
#  The order in which the next imports happen will then determinate
#  the content of the help text.
#  
#  *All* docstrings and all doc_* variables must start and end by newline
#  

from vy.actions.helpers import sa_commands, atomic_commands
# Need to be deleted at the end (previous comment)
# 

from vy import keys as k

from vy.actions.evaluation import __doc__ as doc_evaluation
from vy.actions.evaluation import *

from vy.actions.mode_change import __doc__ as doc_mode_change
from vy.actions.mode_change import *

from vy.actions.with_arg import __doc__ as doc_with_args
from vy.actions.with_arg import *

from vy.actions.motions import __doc__ as doc_motions
from vy.actions.motions import *

from vy.actions.commands import __doc__ as doc_commands
from vy.actions.commands import *

from vy.actions.edition import __doc__ as doc_edition
from vy.actions.edition import *

from vy.actions.linewise import __doc__ as doc_linewise
from vy.actions.linewise import *

@atomic_commands(f'{k.C_L} :redraw :redraw!')
def restart_screen(editor, *args):
    editor.stop_async_io()
    editor.start_async_io()

@sa_commands(f'{k.C_O}')
def go_back_in_jump_list(editor, count=1, *args, **kwargs):
    """
    Goes back in jump list. This motion will not record itself in
    the jump list.
    """
    try:
        buf, lin, col = editor.jump_list[editor.jump_list_pointer]
    except IndexError:
        return
    editor.edit(buf.path)
    editor.current_buffer.cursor_lin_col = lin, col
    editor.jump_list_pointer -= 1
    
@sa_commands(f'{k.C_I}')
def go_forward_in_jump_list(editor, count=1, *args, **kwargs):
    """
    Goes forward in jump list. This motion will not record itself in
    the jump list.
    """
    editor.jump_list_pointer += 1
    if editor.jump_list_pointer == 0:
        editor.jump_list_pointer = -1
    try:
        buf, lin, col = editor.jump_list[editor.jump_list_pointer]
    except IndexError:
        return
    else:
        editor.edit(buf.path)
        editor.current_buffer.cursor_lin_col = lin, col

@sa_commands(f'{k.C_W}>')
def increase_window_width_right(editor, reg=None, part=None, arg=None, count=2):
    """
    Increases/Decreases  window width to the right by {count} columns.
    """
    curwin = editor.current_window
    if curwin.parent is curwin: #if it's screen itself
        return
    curwin.parent.move_v_split_right(count)

@sa_commands(f'{k.C_W}<')
def increase_window_width_left(editor, reg=None, part=None, arg=None, count=2):
    """
    Increases/Decreases window width to the left by {count} columns.
    """
    curwin = editor.current_window
    if curwin.parent is curwin: #if it's screen itself
        return
    curwin.parent.move_v_split_left(count)

@sa_commands('U u :u :un :undo')
def undo(editor, reg=None, part=None, arg=None, count=1):
    """
    Undo last action in the current buffer. {register} argument
    is ignored.
    ---
    NOTE: In Vy there is no difference between 'U' and 'u'
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

@atomic_commands(':pwd :pw :pwd-verbose')
def print_working_directory(editor, reg=None, part=None, arg=None, count=1):
    from pathlib import Path
    editor.screen.minibar(str(Path.cwd()))

@atomic_commands(':files :ls :buffers')
def show_buffers(editor, reg=None, part=None, arg=None, count=1):
    """
    Shows the list of «cached» buffers.
    """
    editor.warning(str(editor.cache))
    return 'normal'

@atomic_commands(f"{k.C_W}n {k.C_W}{k.C_N} :new :enew :ene")
def do_enew(editor, reg=None, part=None, arg=None, count=1):
    """
    Starts editing a new unnamed buffer.
    """
    editor.edit(None)


@atomic_commands(":wa :wall")
def do_save_all(editor, reg=None, part=None, arg=None, count=1):
    """
    Saves all cached buffers.
    """
    for buf in editor.cache:
        if buf.unsaved:
            if buf.path:
                buf.save()
            else:
                editor.warning(f'Cannot save {repr(buf)}')
                editor.edit(buf)
                break

@atomic_commands(':n :ne :next')
def do_edit_next_unsaved_buffer(editor, reg=None, part=None, arg=None, count=1):
    """
    Edit next unsaved buffer. If no buffer is unsaved, exits the editor.
    """
    next_one = False
    for buf in editor.cache:
        if buf.unsaved:
            next_one = buf
            break
    if next_one:
        editor.edit(next_one)
        editor.warning(f'buffer: {repr(editor.current_buffer)} save (:w) or leave! (:q!)')
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


@atomic_commands(':wq :x :xit :exit ZZ')
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


@atomic_commands(":quitall! :quita! :qall! :qa!")
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
    Scrolls the screen one line down. Ajust cursor position so that it is keeps on
    the top line, if it were to escape the current window.
    """
    curwin = editor.current_window
    curbuf = editor.current_buffer
    if curwin.shift_to_lin < curbuf.number_of_lin:
        curwin.shift_to_lin += 1
    current_line_idx, _ = curbuf.cursor_lin_col
    if curwin.shift_to_lin > current_line_idx:
        curbuf.move_cursor('j')

@atomic_commands(f'{k.C_Y}')
def scroll_one_line_up(editor, reg=None, part=None, arg=None, count=1):
    """
    Scrolls the screen one line up. Ajust cursor position so that it is keeps on
    the bottom line, if it were to escape the current window.
    """
    curwin = editor.current_window
    curbuf = editor.current_buffer
    if curwin.shift_to_lin > 0:
        curwin.shift_to_lin -= 1
    current_line_idx, col = curbuf.cursor_lin_col
    # TODO Here is a race condition screen get recenterd to soon...
    if curwin.shift_to_lin + curwin.number_of_lin < current_line_idx:
        curbuf.cursor_lin_col = current_line_idx - 1 , col
        
@atomic_commands(f"z{k.C_M}")
def do_z__CR__(editor, reg=None, part=None, arg=None, count=1):
    """
    Recenters the screen to make cursor line the top line.  (like zt does) but
    cursor is placed on the first non blank caracter of the line.
    """
    curbuf = editor.current_buffer
    do_zt(editor)
    curbuf.cursor = curbuf.find_first_non_blank_char_in_line()

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
    Yanks the text from the cursor to the end of the line, into given
    register, then deletes it and starts 'insert' mode.
    By default, if no register is specified the default "" register is used.
    Optionnal {count} argument is ignored.
    """
    with editor.current_buffer as curbuf:
        editor.registr[reg] = curbuf['cursor:$']
        del curbuf['cursor:$']
        return 'insert'


# TODO Add k.F1 and i_k.F1( but set value in keys.py first ) 
#@with_args_commands(':help :h')
@atomic_commands(':help :h')
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
    ---
    NOTE: To enter a "special key" prepend [CTRL+V].
    """
    from sys import modules
    from vy import help
    from vy.help import resolver
    from pathlib import Path
    try:
        if arg.startswith(':'):
            arg_dest = editor.actions.command[arg[1:]]
        elif arg.startswith('i_'):
            arg_dest = editor.actions.insert[arg[2:]]
        elif arg.startswith('v_'):
            arg_dest = editor.actions.visual[arg[2:]]
        elif arg in modules:
            arg_dest = modules[arg]
        elif ('vy.help.' + arg) in modules:
            arg_dest = modules['vy.help.' + arg]
        elif ('vy.' + arg) in modules:
            arg_dest = modules['vy.' + arg]
        else:
            arg_dest = editor.actions.normal[arg]
    except KeyError:
        editor.warning(f'{arg} not found in help.')
        return 'normal'

    editor.edit(Path(help.__file__).parent / (arg + '.vy.doc'))
    editor.current_buffer.insert(resolver(arg_dest))
    editor.current_buffer.cursor = 0
#    editor.stop_async_io()
#    help(arg)
#    editor.start_async_io()
    return 'normal'

@sa_commands("p :pu :put")
def do_paste_after(editor, reg='"', part=None, arg=None, count=1):
    """
    Paste the text from specified register after the cursor.
    By default, if no register is specified the default "" register is used.
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
    """
    to_insert = editor.registr[reg]
    if to_insert:
        with editor.current_buffer as curbuf:
            if '\n' in to_insert:
                curbuf.cursor = curbuf.find_begining_of_line()
            if curbuf.cursor and curbuf[curbuf.cursor-1] != '\n':
                curbuf.cursor -= 1
            curbuf.insert(editor.registr[reg])

@atomic_commands("gf")
def do_normal_gf(editor, reg=None, part=None, arg=None, count=1):
    """
    Interpret the word the cursor is on as a file name, and try to open it.
    If the file cannot be found in the folder that contains the current buffer,
    Vym will try adding it '.py' suffix. And if the file starts with one or two
    dots (as in a python package), Vym will search in the parents directories.
    """
    from pathlib import Path
    filename = editor.current_buffer['IW'].lstrip().strip()
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
        else:
            editor.screen.minibar(f'file {filename!r} not found.')

########    DEBUGGING ################################################

@atomic_commands(':help!')
def dump_help(editor, reg=None, arg='actions', part=None, count=1):
    """
    Dumps the Vy documentation in a new unnamed buffer.
    """
    editor.edit(None)
    from vy.help import section_builder
    with editor.current_buffer as curbuf:
        curbuf.insert(section_builder(arg))
        curbuf.cursor = 0
        curbuf.string

#@sa_commands('M')
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
        if not isinstance(parent, str):
            value = ('\n' + pformat(parent)).replace('\n', '\n\t')
        else:
            value = '\n' + parent
        to_print += f'\x1b[2m{line}\x1b[0m = {value} \n'
    editor.warning(to_print)

del sa_commands, atomic_commands, k
