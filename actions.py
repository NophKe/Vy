"""
This module contains basic «actions» upon the Vy editor.
An action is a function that accepts an editor as first
argument, and a possibly null, arg string, or slice as
second argument.

As defined in the Vym grammar, some commands require motion
argument, some possibly require a register to work on.
"""

# Here Comes the «full command», taking a slice of the target buffer
# and an optional register. Its up to the function to decide to move 
# the buff.cursor or not, and to determinate what to do if no register
# is being specified.

def change(editor, part, reg='"'):
    curbuf = editor.current_buffer
    stop = part.stop
    start = part.start
    if curbuf[stop - 1] == '\n':
        stop = stop - 1
    editor.register[reg] = curbuf[start:stop]
    del curbuf[start:stop]
    curbuf.cursor = part.start
    return 'insert'

def yank(editor, part, reg='"'):
    text = editor.current_buffer[part]
    editor.current_buffer.cursor = part.stop
    editor.register[reg] = text

def delete(editor, part, reg='"'):
    to_be_del = editor.current_buffer[part]
    editor.current_buffer.__delitem__(part)
    editor.register[reg] = to_be_del

def swap_case(editor, part, reg='"'):
    curbuf = editor.current_buffer
    curbuf[part] = curbuf[part].swapcase()
    curbuf.cursor = part.stop

# Here come command mode commands, those functions must
# take a string represententing the remaining part of the
# command line that invoke them.

def read_file(editor, arg):
    from pathlib import Path
    if not arg:
        editor.warning(':r needs an argument')
        return
    editor.current_buffer.insert(Path(arg).read_text())

#
# Meta Commands
#
def DO_help(editor, arg):
    return help(arg)

def DO_system(editor, arg):
    from os import system
    if arg:
        err = system(arg)
        editor.warning(f'Command Finished with status: {err}')

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
def DO_set(editor, arg):
    if not arg:
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
        setattr(editor.current_buffer, 'set_' + arg, value)
    if value is toggle:
        setattr(editor.current_buffer, 'set_' + arg, not option)

def DO_edit(editor, arg):
    if arg:
        try:
            editor.edit(arg)
        except UnicodeDecodeError:
            editor.warning("Vy cannot deal with this encoding")
        except PermissionError:
            editor.warning("You do not seem to have enough rights to read " + arg)

def DO_enew(editor, arg):
    editor.edit(None)

###
# Saving
#####

def DO_try_to_save(editor, arg):
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

def DO_force_to_save(editor, arg):
    try:
        if arg:
            editor.current_buffer.save_as(arg,override=True)
        else:
            editor.current_buffer.save(override=True)
    except (IsADirectoryError, FileExistsError, PermissionError) as exc:
        editor.warning(f'{exc.__doc__} aborting...')
                
def DO_save_all(editor, cmd):
    for buf in editor.cache:
        if buf.unsaved:
            buf.save()

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

def DO_focus_left_window(editor, arg):
    editor.current_window.get_left_buffer().set_focus()

def DO_focus_right_window(editor, arg):
    editor.current_window.get_right_buffer().set_focus()

def DO_keep_only_current_window(editor, arg):
    while editor.current_window is not editor.screen:
        if editor.current_window is editor.current_window.parent.right_panel:
            editor.current_window.parent.merge_from_right_panel()
        if editor.current_window is editor.current_window.parent.left_panel:
            editor.current_window.parent.merge_from_left_panel()
        
def DO_force_leave_current_window(editor,arg):
    del editor.cache[editor.current_window.buff.cache_id]
    DO_edit_next_unsaved_buffer(editor, arg)

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

def DO_vsplit(editor, arg):
    editor.current_window.vsplit()
    if arg:
        editor.current_window.change_buffer(editor.cache[arg])
###
# Misc
#####

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
        print_tb()
        editor.warning(f'buggy progrm: {Err}')
        return
    python.name_space = name_space
    return python.loop(editor)

def DO_nothing(editor, arg):
    return None

def DO_exit_nice(editor, arg):
    if not any([buffer.unsaved for buffer in editor.cache]):
        DO_exit_hard(editor, arg)
    else:
        DO_edit_next_unsaved_buffer(editor, False)

def DO_exit_hard(editor, arg):
    import sys
    sys.exit(0)

###
# Screen based cursor movements
#####

def DO_zz(editor, arg):
    curwin = editor.current_window 
    middle = (curwin.number_of_lin + 1) / 2
    lin, col = curwin.buff.cursor_lin_col
    new_pos = int(lin - middle)
    if new_pos <= 0:
        curwin.shift_to_lin = 0
    elif new_pos > curwin.buff.number_of_lin:
        curwin.shift_to_lin = curwin.number_of_lin 
    else:
        curwin.shift_to_lin = new_pos 

def DO_zt(editor, arg):
    curwin = editor.current_window 
    lin, col = curwin.buff.cursor_lin_col
    new_pos = lin - 1 
    if new_pos <= 0:
        curwin.shift_to_lin = 0
    elif new_pos > curwin.buff.number_of_lin:
        curwin.shift_to_lin = curwin.number_of_lin 
    else:
        curwin.shift_to_lin = new_pos 

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

def DO_page_down(editor, arg):
    buff = editor.current_buffer
    for _ in range(editor.screen.number_of_lin - 1):
        next_line = buff[buff.cursor:].find('\n')
        if next_line == -1:
            return
        buff.cursor += (next_line + 1)

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
#

DO_suppr  = lambda x, arg: x.current_buffer.suppr()
DO_backspace =  lambda x, arg: x.current_buffer.backspace()

def DO_normal_tilde(editor, reg):
    curbuf = editor.current_buffer
    curbuf[curbuf.cursor] = curbuf[curbuf.cursor].swapcase()
    curbuf.move_cursor('l')

def DO_normal_C(editor, reg='"'):
    curbuf = editor.current_buffer
    editor.register[reg] = curbuf['cursor:$']
    del curbuf['cursor:$']
    return 'insert'

###
# Paste/yank
#

def DO_paste(editor, reg):
    if not reg:
        reg = '"'
    editor.current_buffer.insert(editor.register[reg]),

def DO_insert_expandtabs(editor, arg):
    curbuf = editor.current_buffer
    curbuf.insert('\t')
    orig = curbuf['.']
    after = orig.expandtabs(tabsize=curbuf.set_tabsize)
    curbuf['.'] = after
    curbuf.cursor += len(after) - len(orig)

def DO_normal_gf(editor, reg):
    from pathlib import Path
    filename = editor.current_buffer['iw']
    guess1 = editor.current_buffer.path.with_name(filename)
    guess2 = editor.current_buffer.path.parent / (filename.removeprefix('.') + '.py')
    guess3 = editor.current_buffer.path.parent.parent / (filename.removeprefix('..') + '.py')
    
    for guess in [Path(filename), guess1, guess2, guess3]:
        if guess.exists():
            editor.edit(guess)
            return
    editor.warning(f'file {filename} not found.')

