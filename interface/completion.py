from vy import keys as k

completion_dict = {}

def add_to_dict(*keys):
    def inner(func):
        global completion_dict
        for k_ in keys:
            completion_dict[k_] = func
        return func
    return inner

@add_to_dict(k.up)
def move_up(editor):
    editor.current_buffer.completer_engine.move_cursor_up()
    return True

@add_to_dict('\t')
def switch_or_select(editor):
    if len(editor.current_buffer.completer_engine.completion) == 1:
        return select_item(editor)
    else:
        editor.current_buffer.completer_engine.move_cursor_down()
        return True

@add_to_dict(k.down)
def move_down(editor):
    editor.current_buffer.completer_engine.move_cursor_down()
    return True

@add_to_dict('\r', '\n')
def select_item(editor):
    to_insert, to_delete = editor.current_buffer.completer_engine.select_item()
#    if to_insert and not to_delete:
#        return False
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

def loop(editor):
    while key_press := editor.visit_stdin():
        editor.screen.minibar_completer(editor.current_buffer.get_completions)
        if not editor.screen.minibar_completer:
            editor.screen.minibar(' ( Auto-completion aborted ) No more matches.')
            break
        if key_press in completion_dict:
            if completion_dict[key_press](editor):
                editor.read_stdin()
                continue
            break
            
        if key_press.isprintable():
            editor.current_buffer.undo_list.skip_next()
            editor.current_buffer.insert(editor.read_stdin())
            continue
        break
    editor.screen.minibar_completer.give_up()
    return 'insert'
