from vy import keys as k

completion_dict = {}
insert_dict = {}

def add_to_dict(*keys):
    def inner(func):
        global completion_dict
        for k_ in keys:
            completion_dict[k_] = func
        return func
    return inner

@add_to_dict(k.up)
def move_up(editor):
    editor.screen.minibar_completer.move_cursor_up()
    return True

@add_to_dict('\t')
def switch_or_select(editor):
    if len(editor.screen.minibar_completer.completion) == 1:
        success = select_item(editor)
        if not success:
            do
            
    else:
        editor.screen.minibar_completer.move_cursor_down()
        return True

@add_to_dict(k.down)
def move_down(editor):
    editor.screen.minibar_completer.move_cursor_down()
    return True

@add_to_dict('\r', '\n')
def select_item(editor):
    to_insert, to_delete = editor.screen.minibar_completer.select_item()
    curbuf = editor.current_buffer
    old = curbuf.string
    cursor = curbuf.cursor
    curbuf[cursor - to_delete:cursor] = to_insert
    curbuf.cursor += len(to_insert) - to_delete
    if old == curbuf.string:
        return False
    return True

@add_to_dict(k.backspace)
def backspace(editor):
    editor.current_buffer.backspace()
    return True

@add_to_dict(k.escape, k.C_C)
def give_up(editor):
    editor.screen.minibar(' ( Auto-completion aborted ) User intervention.')
    editor.read_stdin()
    return False

def init(editor):
    global insert_dict
    insert_dict = editor.actions.insert

def loop(editor):
    try:
        editor.current_buffer.set_undo_record(False)
        
        editor.screen.minibar_completer.set_callbacks(
                        lambda: editor.current_buffer.get_completions(), 
                        lambda: editor.current_buffer.check_completions())
               
        while True:
            if not editor.screen.minibar_completer:
                editor.screen.minibar(' ( Auto-completion aborted ) No more matches.')
                break
            else:
                key_press = editor.visit_stdin()
            
            if key_press in completion_dict:
                if completion_dict[key_press](editor):
                    editor.read_stdin()
                    continue
            elif not key_press.isspace() \
                 and key_press not in editor.actions.insert \
                 and key_press.isprintable():
                editor.current_buffer.insert(key_press)
                editor.read_stdin()
                continue
            break
    finally:
        editor.current_buffer.set_undo_record(True)
        editor.screen.minibar_completer.give_up()
        return 'insert'
