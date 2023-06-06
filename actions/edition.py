from vy.actions.helpers import atomic_commands as _atomic_commands
import vy.keys as k
from vy.editor import _Editor

@_atomic_commands(f'i_{k.C_W}')
def erase_word_backward(editor: _Editor, *args, **kwargs):
    """
    Erase one word backward.
    """
    with editor.current_buffer as curbuf:
        start_of_deletion = curbuf.find_previous_delim()
        del curbuf[start_of_deletion:curbuf.cursor]       
        curbuf.cursor = start_of_deletion

@_atomic_commands('i_\n i_\r i_{k.C_J} i_{k.C_M}')
def do_insert_newline(editor, reg=None, part=None, arg=None, count=1):
    """
    Inserts a newline.  If the current buffer has set_autoindent set,
    this will insert same indentation as the previous line.

    """
    with editor.current_buffer as cur_buf:
        line_content = cur_buf.current_line.lstrip()
        if line_content and cur_buf.set_autoindent:
            cur_lin = cur_buf.current_line
            blanks = len(cur_lin) - len(line_content)
            indent = cur_lin[:blanks]
            cur_buf.insert_newline()
            cur_buf.insert(indent)
        elif line_content:
            cur_buf.insert_newline()
        elif cur_buf.set_autoindent:
            cur_buf.cursor = cur_buf.find_begining_of_line()
            cur_buf.current_line = '\n'
            cur_buf.insert_newline()
        else:
            cur_buf.insert_newline()

@_atomic_commands('i_\t')
def do_insert_expandtabs_or_start_completion(editor, reg=None, part=None, arg=None, count=1):
    """
    If 'expand_tabs' is set and the cursor at the start of a line this
    inserts the necessary number of spaces to reach next level of
    indentation, otherwise \\t is used instead.  If used in the middle
    of a line, it will trigger 'completion' sub-mode.
    """
    completer = editor.screen.minibar_completer
    curbuf = editor.current_buffer
    if curbuf.cursor > curbuf.find_first_non_blank_char_in_line():
        completer = curbuf.completer_engine
        completer._async.task_done.wait()
        answers = len(completer.completion)
        if answers:
            if not completer.is_active:
                completer.move_cursor_down()
            if answers == 1:
                completer.select_item()
            return 'insert'
        
    with editor.current_buffer as curbuf:
        curbuf.insert('\t')
        if curbuf.set_expandtabs:
            curlin = curbuf.current_line
            origin_len = len(curlin)
            curbuf.current_line = curlin.expandtabs(tabsize=curbuf.set_tabsize)
            new_len = len(curbuf.current_line)
            curbuf.cursor += (new_len - origin_len)

@_atomic_commands(f'i_{k.C_A}')
def insert_last_inserted_text(editor, **kwargs):
    """
    Re-insert last inserted text at cursor position.
    """
    editor.current_buffer.insert(editor.registr['.'])

@_atomic_commands(f'i_{k.C_R}')
def insert_from_register(editor, **kwargs):
    """
    Reads next key from keyboard, if it is a valid register, inserts it.
    """
    txt = str(editor.registr) + '\n\tSelect register to paste from'
    cancel = editor.screen.minibar(*(txt.splitlines()))
    try:
        editor.current_buffer.insert(editor.registr[editor.read_stdin()])
    except AssertionError: # Key is not a valid register
        editor.screen.minibar('( Nothing inserted. )')
    else:
        cancel()

@_atomic_commands(f'i_{k.suppr} x')
def do_suppr(editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes the character under the cursor, joining current line with
    the next one if on the last position of the line.  Does nothing if
    on the last position of the buffer.
    """
    editor.current_buffer.suppr()

@_atomic_commands(f'i_{k.backspace} i_{k.linux_backpace} X')
def do_backspace(editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes the character on the left of the cursor, joining current
    line with the previous one if on the first position of the line.
    Does nothing if on the first position of the buffer.
    """
    with editor.current_buffer as curbuf:
        if curbuf.set_autoindent:
            lin, col = editor.current_buffer.cursor_lin_col
            col = col - 1 if col > 0 else 0
            before_cursor = editor.current_buffer.current_line[:col]
            if before_cursor and not before_cursor.strip():
                return editor.actions.normal('<<')
        editor.current_buffer.backspace()

@_atomic_commands("r")
def do_r(editor, reg=None, part=None, arg=None, count=1):
    """
    Replace the character under the cursor by next keystrike.
    """
    editor.current_buffer[editor.current_buffer.cursor] = editor.read_stdin()
    

@_atomic_commands(f'i_{k.C_Z}')
def increment(editor, reg=None, part=None, arg=None, count=1):
    """
    If the cursor is on a number, increment it leaving the cursor in
    place.
    """ 
    cur_word = editor.current_buffer[editor.current_buffer.inner_word].replace('\n','')
    editor.warning(repr(cur_word))
    if cur_word.isnumeric():
        editor.current_buffer['iw'] = str(int(cur_word)+1)

@_atomic_commands(f'{k.C_up}')
def move_line_up(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the current line, one line up
    """
    with editor.current_buffer as curbuf:
        cur_lin_idx = curbuf.current_line_idx
        if cur_lin_idx > 0:
            line_1 = curbuf.splited_lines[cur_lin_idx]
            line_2 = curbuf.splited_lines[cur_lin_idx - 1]
            
            curbuf.splited_lines[cur_lin_idx] = line_2
            curbuf.splited_lines[cur_lin_idx - 1] = line_1
            curbuf.string = ''.join(curbuf.splited_lines)

            curbuf.cursor_lin_col = (cur_lin_idx - 1, 0)
            if curbuf.current_line.strip():
                curbuf.move_cursor('_')
            
@_atomic_commands(f'{k.C_down}')
def move_line_down(editor, reg=None, part=None, arg=None, count=1):
    """
    Moves the current line, one line down.
    """
    with editor.current_buffer as curbuf:
        cur_lin_idx = curbuf.current_line_idx
        if cur_lin_idx < curbuf.number_of_lin - 1:
            line_1 = curbuf.splited_lines[cur_lin_idx]
            line_2 = curbuf.splited_lines[cur_lin_idx + 1]
            
            curbuf.splited_lines[cur_lin_idx] = line_2
            curbuf.splited_lines[cur_lin_idx + 1] = line_1
            curbuf.string = ''.join(curbuf.splited_lines)
            
            curbuf.cursor_lin_col = (cur_lin_idx + 1, 0)
            if curbuf.current_line.strip():
                curbuf.move_cursor('_')

