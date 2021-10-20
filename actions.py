"""
This module contains basic «actions» upon the Vy editor.
An action is a function that accepts an editor as first
argument, and a possibly null, arg string, or slice as
second argument.

As defined in the Vym grammar, some commands require motion
argument, some possibly require a register to work on.
"""
from .helpers import ( sa_commands, full_commands,
                      with_args_commands, atomic_commands)
from . import keys as k

# Here Comes the «full command», taking a slice of the target buffer
# and an optional register. Its up to the function to decide to move 
# the buff.cursor or not, and to determinate what to do if no register
# is being specified.

@with_args_commands(':nmap :nnoremap')
def DO_nmap(ed, arg):
    if not arg or not ' ' in arg:
        ed.warning('[SYNTAX]    :nmap [key] [mapping]')
    key, value = arg.split(' ', maxsplit=1)
    ed.current_buffer.stand_alone_commands[key] = lambda ed,cmd: ed.push_macro(value)

@atomic_commands(':reg :registers')
def show_registers(ed, cmd):
    ed.warning(str(ed.register))
    return 'normal'

@atomic_commands(':files :ls :buffers')
def show_buffers(ed, cmd):
    ed.warning(str(ed.cache))
    return 'normal'

@atomic_commands(':vi :visual')
def normal_mode(ed, cmd):
    return 'normal'

@atomic_commands(':python :py')
def python_mode(ed, cmd):
    return 'python'

@full_commands('c')
def change(editor, part, reg='_'):
    """
    Deletes the text from the cursor position to MOTION argument,
    or inside MOTION if it resolves to as slice of the text.
    The discarded text is also copied to the {register}.
    Then starts 'insert' mode.
    By default, if no register is specified the black hole "_ register is used.
    """
    curbuf = editor.current_buffer
    stop = part.stop
    start = part.start
    if curbuf[stop - 1] == '\n':
        stop = stop - 1
    editor.register[reg] = curbuf[start:stop]
    del curbuf[start:stop]
    curbuf.cursor = part.start
    return 'insert'

@full_commands('y')
def yank(editor, part, reg='"'):
    """
    Yanks (copies) the text from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    By default, if no register is specified the default "" register is used.
    """
    text = editor.current_buffer[part]
    editor.current_buffer.cursor = part.stop
    editor.register[reg] = text

@full_commands('d')
def delete(editor, part, reg='"'):
    """
    Deletes the text from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    The discarded text is also copied to the {register}.
    By default, if no register is specified the default "" register is used.
    """
    to_be_del = editor.current_buffer[part]
    editor.current_buffer.__delitem__(part)
    editor.register[reg] = to_be_del

@full_commands('gu')
def lower_case(editor, part, reg='_'):
    """
    Makes the text lower case from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    {register} argument is ignored.
    """
    curbuf = editor.current_buffer
    curbuf[part] = curbuf[part].lower()
    curbuf.cursor = part.stop

@full_commands('gU')
def upper_case(editor, part, reg='_'):
    """
    Makes the text upper case from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    {register} argument is ignored.
    """
    curbuf = editor.current_buffer
    curbuf[part] = curbuf[part].upper()
    curbuf.cursor = part.stop

@full_commands('g~')
def swap_case(editor, part, reg='_'):
    """
    Swaps the case of the text from the cursor position to {movement} argument,
    or inside {movement} if it resolves to as slice of the text.
    {register} argument is ignored.
    """
    curbuf = editor.current_buffer
    curbuf[part] = curbuf[part].swapcase()
    curbuf.cursor = part.stop

# Here come command mode commands, those functions must
# take a string represententing the remaining part of the
# command line that invoke them.

@with_args_commands(":read :r")
def read_file(editor, arg):
    """
    Reads the content of file specified as argument and inserts it at the current
    cursor location.
    TODO: No check is done by this function. May raise exception!
    """
    from pathlib import Path
    if not arg:
        editor.warning(':r needs an argument')
        return
    editor.current_buffer.insert(Path(arg).read_text())

#
# Meta Commands
#
@with_args_commands(":!")
def DO_system(editor, arg):
    from os import system
    if arg:
        err = system(arg)
        editor.warning(f'Command Finished with status: {err}')

@with_args_commands(":chdir")
def DO_chdir(editor, arg):
    if not arg:
        return
    import os
    try:
        os.chdir(arg)
    except FileNotFoundError:
        editor.warning(f'File not found: {arg}')

# Editor
####
@with_args_commands(":set :se")
def DO_set(editor, arg):
    if not arg:
        editor.warning("""
    [SYNTAX]        :set {argument}   >>> set to True
    [SYNTAX]        :set no{argument} >>> set to False
    [SYNTAX]        :set {argument}!  >>> toggle True/False""")
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
        editor.warning(f"invalid option {arg}")
        return

    if isinstance(option, type(value)):
        setattr(editor.current_buffer, f'set_{arg}', value)
    if value is toggle:
        setattr(editor.current_buffer, f'set_{arg}', not option)


@with_args_commands(":e :edit :ex")
def DO_edit(editor, arg):
    if arg:
        try:
            editor.edit(arg)
        except UnicodeDecodeError:
            editor.warning("Vy cannot deal with this encoding")
        except PermissionError:
            editor.warning("You do not seem to have enough rights to read " + arg)

@atomic_commands(":enew")
def DO_enew(editor, arg):
    editor.edit(None)

###
# Saving
#####

@atomic_commands(':w :write')
@with_args_commands(':w :write')
def DO_try_to_save(editor, arg):
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

@atomic_commands(":w! :write:")
@with_args_commands(":w! :write:")
def DO_force_to_save(editor, arg):
    try:
        if arg:
            editor.current_buffer.save_as(arg,override=True)
        else:
            editor.current_buffer.save(override=True)
    except (IsADirectoryError, FileExistsError, PermissionError) as exc:
        editor.warning(f'{exc.__doc__} aborting...')
                
@sa_commands(":wall")
def DO_save_all(editor, cmd):
    for buf in editor.cache:
        if buf.unsaved:
            buf.save()

@atomic_commands(':next')
def DO_edit_next_unsaved_buffer(editor,arg):
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
            DO_exit_nice(editor, arg)
###
# Window Manip
#####

@atomic_commands(f'{k.C_W}{k.C_H} {k.C_W}{k.C_left} {k.C_W}h')
def DO_focus_left_window(editor, arg):
    editor.current_window.get_left_buffer().set_focus()

@atomic_commands(f'{k.C_W}{k.C_L} {k.C_W}{k.C_right} {k.C_W}l')
def DO_focus_right_window(editor, arg):
    editor.current_window.get_right_buffer().set_focus()

@atomic_commands(f'{k.C_W}o {k.C_W}{k.C_O} :only')
def DO_keep_only_current_window(editor, arg):
    while editor.current_window is not editor.screen:
        if editor.current_window is editor.current_window.parent.right_panel:
            editor.current_window.parent.merge_from_right_panel()
        if editor.current_window is editor.current_window.parent.left_panel:
            editor.current_window.parent.merge_from_left_panel()
        
@atomic_commands('ZQ')
def DO_force_leave_current_window(editor,arg):
    del editor.cache[editor.current_window.buff.cache_id]
    DO_edit_next_unsaved_buffer(editor, arg)

@atomic_commands(':q :quit')
def DO_leave_current_window(editor, arg):
    curwin = editor.current_window
    if curwin is editor.screen:
        if curwin.buff.unsaved:
            editor.warning('save this buffer (:w) or force (:q!)')
        else:
            DO_exit_nice(editor, arg)
    elif curwin.parent.left_panel is curwin:
        curwin.parent.merge_from_right_panel()
    else:
        curwin.parent.merge_from_left_panel()

@atomic_commands(f':vsplit :vs {k.C_W}v')
@with_args_commands(':vsplit')
def DO_vsplit(editor, arg):
    editor.current_window.vsplit()
    if arg:
        editor.current_window.change_buffer(editor.cache[arg])
###
# Misc
#####

@atomic_commands(":eval")
def DO_eval_buffer(editor,arg):
    from .interface import python
    from traceback import print_tb
    #import __main__
    #return exec(editor.current_buffer.getvalue(), __main__.__dict__)
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

@atomic_commands(":q :quit :quitall :quita :qall :qa")
def DO_exit_nice(editor, arg):
    if not any([buffer.unsaved for buffer in editor.cache]):
        DO_exit_hard(editor, arg)
    else:
        DO_edit_next_unsaved_buffer(editor, False)

@atomic_commands(":q! :quit! :quitall! :quita! :qall! :qa!")
def DO_exit_hard(editor, arg):
    import sys
    sys.exit(0)

###
# Screen based cursor movements
#####
@atomic_commands("zz")
def DO_zz(editor, arg):
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

@atomic_commands("zt")
def DO_zt(editor, arg):
    curwin = editor.current_window 
    lin, _ = curwin.buff.cursor_lin_col
    new_pos = lin - 1 
    if new_pos <= 0:
        curwin.shift_to_lin = 0
    elif new_pos > curwin.buff.number_of_lin:
        curwin.shift_to_lin = curwin.number_of_lin 
    else:
        curwin.shift_to_lin = new_pos 

@atomic_commands("zb")
def DO_zb(editor, arg):
    curwin = editor.current_window 
    lin, col = curwin.buff.cursor_lin_col
    new_pos = lin - curwin.number_of_lin
    if new_pos <= 0:
        curwin.shift_to_lin = 0
    elif new_pos > curwin.buff.number_of_lin:
        curwin.shift_to_lin = curwin.number_of_lin 
    else:
        curwin.shift_to_lin = new_pos 

@atomic_commands(f'{k.page_up}')
def DO_page_down(editor, arg):
    buff = editor.current_buffer
    for _ in range(editor.screen.number_of_lin - 1):
        next_line = buff[buff.cursor:].find('\n')
        if next_line == -1:
            return
        buff.cursor += (next_line + 1)

@atomic_commands(f'{k.page_down}')
def DO_page_up(editor, arg):
    buff = editor.current_buffer
    for _ in range(editor.screen.number_of_lin):
        prev_line = buff[:buff.cursor].rfind('\n')
        if prev_line == -1:
            return
        buff.cursor = prev_line
    if buff.cursor > 0:
        buff.cursor += 1

###
# Normal Mode sub-loops
#####

@atomic_commands("zz")
def DO_normal_n(editor,arg):
    try:
        needle = editor.register['/']
    except KeyError:
        return

    if not needle:
        return
    curbuf = editor.current_buffer

    offset = curbuf._string[curbuf.cursor+1:].find(needle)
    if offset == -1:
        editor.warning('string not found')
        return 'normal'
    curbuf.cursor += offset + 1
 
def DO_find(editor,arg):
    editor.screen.minibar('/')
    curbuf = editor.current_buffer
    try:
        needle = input()
    except KeyboardInterrupt:
        return 'normal'

    if not needle:
        return 'normal'
    editor.register['/'] = needle

    offset = curbuf._string[curbuf.cursor+1:].find(needle)
    if offset == -1:
        editor.warning('string not found')
        return 'normal'
    curbuf.cursor += offset + 1

@sa_commands("r")
def DO_r(editor, arg):
    editor.current_buffer['cursor'] = editor.read_stdin()
    
def DO_f(curbuf):
    from __main__ import Editor as editor
    char_to_seek = editor.read_stdin()
    char_relative = curbuf['cursor:#+1'].find(char_to_seek)
    if char_relative > 0:
        return curbuf.cursor + char_relative        
    return curbuf.cursor

###
# Edition

@atomic_commands(f'i_{k.backspace}')
def DO_backspace(editor, arg):
    """
    Deletes the character on the left of the cursor, joining current line
    with the previous one if on the first position of the line.
    Does nothing if on the first position of the buffer.
    """
    editor.current_buffer.backspace()

    
@atomic_commands(f'i_{k.suppr}')
def DO_suppr(editor, arg):
    """
    Deletes the character under the cursor, joining current line with the
    next one if on the last position of the line.
    Does nothing if on the last position of the buffer.
    """
    editor.current_buffer.suppr()
    
@sa_commands("~")
def DO_normal_tilde(editor, reg):
    """
    Makes the character under the cursor upper case, and moves the cursor 
    one character right unless if on the last position of the line.
    Optionnal "{register} argument is ignored.
    """
    curbuf = editor.current_buffer
    curbuf[curbuf.cursor] = curbuf[curbuf.cursor].upper()
    curbuf.move_cursor('l')

@sa_commands("C")
def DO_normal_C(editor, reg='"'):
    """
    Yanks the text from the cursor to the register, the delete it and starts
    'insert' mode.
    By default, if no register is specified the default "" register is used.
    """
    curbuf = editor.current_buffer
    editor.register[reg] = curbuf['cursor:$']
    del curbuf['cursor:$']
    return 'insert'

###
# Paste/yank
#


@atomic_commands(':help :h')
@with_args_commands(':help :h')
def help(ed, cmd):
    """
    [SYNTAX] :help TOPIC

    For help about a command mode command prepend: i_
        :help :help

    For help about a insert mode command prepend: i_
        :help i_^R

    For help about a visual mode command prepend: v_
        :help v_O

    For help about a normal mode command just type it!
        :help ~
    """
    topic = ':help' if not cmd else cmd

    try:
        if topic.startswith(':'):
            topic = ed.actions.command[topic[1:]]
        elif topic.startswith('i_'):
            topic = ed.actions.insert[topic[2:]]
        elif topic.startswith('v_'):
            topic = ed.actions.visual[topic[2:]]
        else:
            topic = ed.actions.normal[topic]
    except KeyError:
        ed.warning(f'{topic} not found in help.')
        return 'normal'
    ed.screen.original_screen() 
    help(topic)
    ed.screen.alternative_screen()
    return 'normal'

@sa_commands("p")
def DO_paste(editor, reg):
    """
    Paste the text from specified register after the cursor.
    By default, if no register is specified the default "" register is used.
    """
    editor.current_buffer.insert(editor.register[reg]),

@atomic_commands('i_\t')
def DO_insert_expandtabs(editor, arg):
    curbuf = editor.current_buffer
    curbuf.insert('\t')
    orig = curbuf['.']
    after = orig.expandtabs(tabsize=curbuf.set_tabsize)
    curbuf['.'] = after
    curbuf.cursor += len(after) - len(orig)

@atomic_commands("gf")
def DO_normal_gf(editor, reg):
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
    editor.warning(f'file {filename!r} not found.')


del sa_commands, full_commands, atomic_commands, with_args_commands
