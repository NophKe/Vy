from vy.keys import _escape
from vy.editor import _Editor
from vy.interface.helpers import one_inside_dict_starts_with
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
def move_up(editor: _Editor):
    completer = editor.current_buffer.completer_engine
    if completer.selected != -1:
        completer.move_cursor_up()
        return True

@add_to_dict('\t')
def switch_or_select(editor: _Editor):
    completer = editor.current_buffer.completer_engine
    lin, col = editor.current_buffer.cursor_lin_col
    completer._async.complete_work()
    if editor.current_buffer.current_line[:col].strip():
        if len(completer.completion) == 1:
            return select_item(editor)
        elif completer.completion:
            editor.current_buffer.completer_engine.move_cursor_down()
            return True

@add_to_dict(k.C_N)
def select_first_or_previous(editor: _Editor):
    completer = editor.current_buffer.completer_engine
    if completer.selected == -1:
        completer.selected = 0
        return True
    return move_down(editor)

@add_to_dict(k.C_P)
def select_last_or_next(editor: _Editor):
    completer = editor.current_buffer.completer_engine
    if completer.selected == -1:
        completer.selected = len(completer.completion) - 1
        return True
    return move_up(editor)

@add_to_dict(k.down)
def move_down(editor: _Editor):
    completer = editor.current_buffer.completer_engine
    if completer.selected != -1:
        editor.current_buffer.completer_engine.move_cursor_down()
        return True
    
@add_to_dict('\r', '\n', k.C_J, k.C_M)
def select_item(editor: _Editor):
    to_insert, to_delete = editor.current_buffer.completer_engine.select_item()
    if len(to_insert) == to_delete:
        return False
    curbuf = editor.current_buffer
    cursor = curbuf.cursor
    curbuf[cursor - to_delete:cursor] = to_insert
    curbuf.cursor += len(to_insert) - to_delete
    return True

@add_to_dict(k.C_Y)
def validate_selection(editor: _Editor):
    completer = editor.current_buffer.completer_engine
    if completer.is_active:
        return select_item(editor)
    
@add_to_dict(k.C_C)
def give_up(editor: _Editor):
    editor.screen.minibar(' ( Auto-completion aborted )')
    minibar_completer.give_up()
    editor.current_buffer.completer_engine.selected = -1
    return True    

def monoline_loop(editor: _Editor):
    last_insert = ''
    minibar_completer(editor.current_buffer.get_completions)
    while True:
        key_press = editor.read_stdin()
        if key_press in completion_dict:
            if completion_dict[key_press](editor):
                continue
        
        elif key_press.isprintable():
            editor.current_buffer.undo_list.skip_next()
            editor.current_buffer.insert(key_press)
            last_insert += key_press
            continue
        break
    if last_insert.strip():
        editor.registr['.'] = last_insert
    return key_press

def init(editor: _Editor):
    global minibar, dictionary, minibar_completer
    minibar_completer = editor.screen.minibar_completer
    minibar = editor.screen.minibar
    dictionary = editor.actions.insert
    
def loop(editor: _Editor):
    global completer_engine
    completer_engine = editor.current_buffer.completer_engine
    minibar_completer(completer_engine.get_raw_screen)
        
    while True:
        user_input = monoline_loop(editor) 
        cancel_minibar = minibar(f' __ Processing command: {_escape(user_input)} __')
        try:
            action = dictionary[user_input]
        except KeyError:
            minibar(f' ( Invalid command: {_escape(user_input)} )')
        else:
            mode = action(editor) or 'insert'
            cancel_minibar()
            if mode != 'insert':
                break
    
    minibar_completer.give_up()
    completer_engine.selected = -1
    return mode

