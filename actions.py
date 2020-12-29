TRUE_no_unsaved_buffer_in_cache = lambda editor: False if any( [buffer.unsaved for buffer in editor.cache] ) else True

# Editor
####
def DO_set(editor, arg):
    toggle = object()
    if not arg: return
    
    arg = arg.strip()
    if ' ' in arg:
        arg, value = arg.split(' ', maxsplit=1)
        value = int(value)
    elif arg.lower().startswith('no'):
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
    try:
        editor.edit(arg)
    except (IsADirectoryError, PermissionError) as exc:
        editor.warning(f'sorry! {exc.__doc__} ')

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
        editor.edit(next_one)
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
    editor.cache.pop(editor.current_window.buff.cache_id)
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
        editor.current_window.change_buffer(editor.cache.get(arg))
###
# Misc
#####

def DO_eval_buffer(editor,arg):
    #import __main__
    #return exec(editor.current_buffer.getvalue(), __main__.__dict__)
    try:
        return exec(editor.current_buffer.getvalue(), {})
    except Exception as Err:
        editor.warning(f'buggy progrm: {Err}')

def DO_nothing(editor, arg):
    return None

def DO_exit_nice(editor, arg):
    if TRUE_no_unsaved_buffer_in_cache(editor):
        DO_exit_hard(editor, arg)
    else:
        DO_edit_next_unsaved_buffer(editor, False)

def DO_exit_hard(editor, arg):
    import sys
    return sys.exit(0)

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
    for _ in range(editor.screen.number_of_lin - 1):
        prev_line = buff[:buff.cursor].rfind('\n')
        if prev_line == -1:
            return
        buff.cursor = prev_line

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
    from .console import get_a_key
    editor.current_buffer.write(get_a_key())
    editor.current_buffer.seek(editor.current_buffer.tell() - 1)    
    
def DO_f(editor, arg):
    from .console import get_a_key 
    char_to_seek = get_a_key()
    curbuf = editor.current_buffer
    old_pos = curbuf.tell()

    while True:
        next_char = curbuf.read(1)
        if not next_char:
            curbuf.seek(old_pos)
            return
        elif next_char == char_to_seek:
            curbuf.seek(curbuf.tell() - 1)
            return
        else:
            continue

###
# Edition
#

DO_suppr  = lambda x, arg: x.current_buffer.suppr()
DO_backspace =  lambda x, arg: x.current_buffer.backspace()

def DO_normal_tilde(editor, arg):
    curbuf = editor.current_buffer
    curbuf[curbuf.cursor] = curbuf[curbuf.cursor].swapcase()
    curbuf.move_cursor('l')

###
# Paste/yank
#

def DO_paste(editor, arg):
    try:
        txt = editor.register['"']
    except KeyError:
        return
    editor.current_buffer.insert(editor.register['"']),

def DO_insert_expandtabs(editor, arg):
    curbuf = editor.current_buffer
    curbuf.insert('\t')
    orig = curbuf['.']
    after = orig.expandtabs(tabsize=curbuf.tab_size)
    curbuf['.'] = after
    curbuf.cursor += len(after) - len(orig)

