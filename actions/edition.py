from vy.actions.helpers import atomic_commands
import vy.keys as k

@atomic_commands(f'i_{k.C_W}')
def erase_word_backward(editor, *args, **kwargs):
    """
    Erase one word backward.
    """
    with editor.current_buffer as curbuf:
        del curbuf[curbuf.find_previous_delim():curbuf.cursor]       

@atomic_commands('i_\n i_\r i_{k.C_J} i_{k.C_M}')
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

@atomic_commands('i_\t')
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
        return 'completion'
    with editor.current_buffer as curbuf:
        curbuf.insert('\t')
        if curbuf.set_expandtabs:
            curlin = curbuf.current_line
            origin_len = len(curlin)
            curbuf.current_line = curlin.expandtabs(tabsize=curbuf.set_tabsize)
            new_len = len(curbuf.current_line)
            curbuf.cursor += (new_len - origin_len)

@atomic_commands(f'i_{k.C_A}')
def insert_last_inserted_text(editor, **kwargs):
    """
    Re-insert last inserted text at cursor position.
    """
    editor.current_buffer.insert(editor.registr['.'])

@atomic_commands(f'i_{k.C_R}')
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

@atomic_commands(f'i_{k.suppr} x')
def do_suppr(editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes the character under the cursor, joining current line with
    the next one if on the last position of the line.  Does nothing if
    on the last position of the buffer.
    """
    editor.current_buffer.suppr()

@atomic_commands(f'i_{k.backspace} i_{k.linux_backpace} X')
def do_backspace(editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes the character on the left of the cursor, joining current
    line with the previous one if on the first position of the line.
    Does nothing if on the first position of the buffer.
    """
    with editor.current_buffer as curbuf:
        if curbuf.set_autoindent:
            _, start_of_line = curbuf.current_line_off
            start_of_line = curbuf.string[start_of_line:curbuf.cursor]
            editor.screen.minibar(start_of_line)
            content = start_of_line.strip()
            if start_of_line and not content:
                from vy.actions.linewise import dedent_current_line
                return dedent_current_line(editor)
        editor.current_buffer.backspace()
        

@atomic_commands("r")
def do_r(editor, reg=None, part=None, arg=None, count=1):
    """
    Replace the character under the cursor by next keystrike.
    """
    editor.current_buffer[editor.current_buffer.cursor] = editor.read_stdin()
    

@atomic_commands(f'i_{k.C_Z}')
def increment(editor, reg=None, part=None, arg=None, count=1):
    """
    If the cursor is on a number, increment it leaving the cursor in
    place.
    """ 
    #>>> this is buggy because iw is buggy         # bug
    cur_word = editor.current_buffer['iw']      .replace('\n','')
    editor.warning(repr(cur_word))
    if cur_word.isnumeric():
        editor.current_buffer['iw'] = str(int(cur_word)+1)
        
