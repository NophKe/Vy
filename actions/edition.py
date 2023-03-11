from vy.actions.helpers import atomic_commands
import vy.keys as k

@atomic_commands('i_\n i_\r i_{k.C_J} i_{k.C_M}')
def do_insert_newline(editor, reg=None, part=None, arg=None, count=1):
    """
    Inserts a newline. If the current buffer has set_autoindent set, this
    will insert same indentation as the previous line.

    """
    with editor.current_buffer as cur_buf:
        if cur_buf.set_autoindent:
            cur_lin = cur_buf.current_line
            blanks = len(cur_lin) - len(cur_lin.lstrip())
            indent = cur_lin[:blanks]
            cur_buf.insert_newline()
            cur_buf.insert(indent)
        else:
            cur_buf.insert_newline()

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
        if before.strip():
            completer.set_callbacks(lambda: curbuf.get_completions(), lambda: curbuf.check_completions())
            if completer:
                return 'completion'
            else:
                completer.give_up()

    with editor.current_buffer as curbuf:
        curbuf.insert('\t')
        if curbuf.set_expandtabs:
            orig = curbuf['0:$']  # TODO should use current_line.setter property
            after = orig.expandtabs(tabsize=curbuf.set_tabsize)
            curbuf['0:$'] = after
            curbuf.cursor += len(after) - len(orig)
@atomic_commands(f'i_{k.C_A}')
def insert_last_inserted_text(editor, **kwargs):
    """
    Re-insert last inserted text at cursor position.
    """
    editor.push_macro(editor.registr['.'])

@atomic_commands(f'i_{k.suppr} x')
def do_suppr(editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes the character under the cursor, joining current line with the
    next one if on the last position of the line.
    Does nothing if on the last position of the buffer.
    """
    editor.current_buffer.suppr()

@atomic_commands(f'i_{k.backspace} i_{k.linux_backpace} X')
def do_backspace(editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes the character on the left of the cursor, joining current line
    with the previous one if on the first position of the line.
    Does nothing if on the first position of the buffer.
    """
    editor.current_buffer.backspace()

@atomic_commands(f'{k.C_A} i_{k.C_A}')
def increment(editor, reg=None, part=None, arg=None, count=1):
    """
    If the cursor is on a number, increment it leaving the cursor in place.
    """ 
# this is buggy because iw is buggy         # bug
    cur_word = editor.current_buffer['iw']      .replace('\n','')
#    editor.warning(repr(cur_word))
    if cur_word.isnumeric():
        editor.current_buffer['iw'] = str(int(cur_word)+1)
