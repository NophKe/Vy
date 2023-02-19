from vy.interface.helpers import one_inside_dict_starts_with
from vy import keys as k

completion_dict = {}
insert_dict = {}

def add_to_dict(*keys):
    def inner(func):
        global completion_dict
        for k in keys:
            completion_dict[k] = func
        return func
    return inner

@add_to_dict(k.up)
def move_up(editor):
    editor.screen.minibar_completer.move_cursor_up()

@add_to_dict('\t')
def switch_or_select(editor):
    if not editor.screen.minibar_completer.completion:
        return 'insert'
    elif len(editor.screen.minibar_completer.completion) == 1:
        select_item(editor, or_new_line=False)
    else:
        editor.screen.minibar_completer.move_cursor_down()

@add_to_dict(k.down)
def move_down(editor):
    editor.screen.minibar_completer.move_cursor_down()

@add_to_dict('\r', '\n')
def select_item(editor, or_new_line=True):
    to_insert, to_delete = editor.screen.minibar_completer.select_item()
    curbuf = editor.current_buffer
    old = curbuf.string
    cursor = curbuf.cursor
    curbuf[cursor - to_delete:cursor] = to_insert
    curbuf.cursor += len(to_insert) - to_delete
    if old == curbuf.string and or_new_line:
        curbuf.insert_newline()
        return 'insert'

@add_to_dict(k.backspace)
def backspace(editor):
    editor.current_buffer.backspace()

@add_to_dict(k.escape)
def give_up(editor):
    editor.screen.minibar('giving up completion, press ESC again for normal mode')
    return 'insert'

def init(editor):
    global insert_dict
    insert_dict = editor.actions.insert

def loop(editor):
    try:
        while True:
            if not editor.screen.minibar_completer.completion:
                return 'insert'
            key_press = editor.read_stdin()
            if key_press in completion_dict:
                rv = completion_dict[key_press](editor)
                if rv:
                    return rv
                continue
            elif key_press.isalnum() or key_press == '.':
                editor.current_buffer.insert(key_press)
                continue
            elif key_press in insert_dict:
                insert_dict[key_press](editor)
                return 'insert'
            elif key_press.isprintable():
                editor.current_buffer.insert(key_press)
                return 'insert'
            else:
                editor.screen.minibar(f'unrecognized key: {k._escape(key_press)}')
                return 'insert'
    finally:
        editor.screen.minibar_completer.give_up()
