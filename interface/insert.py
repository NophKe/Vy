from vy.utils import async_update
from vy.keys import _escape
from vy.editor import _Editor
from vy.interface.helpers import one_inside_dict_starts_with
from vy.utils import Cancel
from vy import keys as k

class Completer:
    def __init__(self, buffer):
        self.buff = buffer
        self.selected = -1
        self.completion = []
        self.prefix_len = 0
        self._last = []
        
    def update(self):
        completion, prefix_len = self.buff.auto_complete()
        if self._last != (completion, prefix_len):
            self._last = (completion, prefix_len)
            self.completion = completion
            self.prefix_len = prefix_len
            self.selected = -1
        minibar_completer.set_value(completion, self.selected)
        
    @property
    def is_active(self):
        return self.completion and self.selected != -1
               
    def move_cursor_up(self):
        if self.selected > 0:
            self.selected -= 1
        else:
            self.selected = len(self.completion) - 1

    def move_cursor_down(self):
        if self.selected == len(self.completion) - 1:
            self.selected = 0
        else:
            self.selected += 1

    def select_item(self):
        if self.is_active:
            return self.completion[self.selected], self.prefix_len
        return '', 0
        
completion_dict = {}
def add_to_dict(*keys):
    def inner(func):
        global completion_dict
        for k_ in keys:
            completion_dict[k_] = func
        return func
    return inner

@add_to_dict(' ')
def select_and_space(editor: _Editor):
    select_item(editor)
    editor.current_buffer.insert(' ')
    return True
    
@add_to_dict('.')
def select_and_dot(editor: _Editor):
    select_item(editor)
    editor.current_buffer.insert('.')
    return True
    
@add_to_dict(k.up)
def move_up(editor: _Editor):
    if completer_engine.selected != -1:
        completer_engine.move_cursor_up()
        return True

@add_to_dict('\t')
def switch_or_select(editor: _Editor):
    lin, col = editor.current_buffer.cursor_lin_col
    if not editor.current_buffer.current_line[:col-1].strip():
        return False

    if completer_engine.completion and completer_engine.selected == -1:
        completer_engine.move_cursor_up()
        
    if editor.current_buffer.current_line[:col].strip():
        if len(completer_engine.completion) == 1:
            return select_item(editor)
        elif completer_engine.completion:
            completer_engine.move_cursor_down()
            return True

@add_to_dict(k.C_N)
def select_first_or_previous(editor: _Editor):
    if completer_engine.selected == -1:
        completer_engine.selected = 0
        return True
    return move_down(editor)


@add_to_dict(k.C_P)
def select_last_or_next(editor: _Editor):
    if completer_engine.selected == -1:
        completer_engine.selected = len(completer_engine.completion) - 1
        return True
    return move_up(editor)

@add_to_dict(k.down)
def move_down(editor: _Editor):
    if completer_engine.selected != -1:
        completer_engine.move_cursor_down()
        return True
    
@add_to_dict('\r', '\n', k.C_J, k.C_M)
def select_item(editor: _Editor):
    if not completer_engine.is_active:
        return False
    to_insert, to_delete = completer_engine.select_item()
    if len(to_insert) == to_delete:
        return False
    curbuf = editor.current_buffer
    cursor = curbuf.cursor
    curbuf[cursor - to_delete:cursor] = to_insert
    curbuf.cursor += len(to_insert) - to_delete
    return True

@add_to_dict(k.C_Y)
def validate_selection(editor: _Editor):
    if completer_engine.is_active:
        return select_item(editor)
    
@add_to_dict(k.C_C)
def give_up(editor: _Editor):
    editor.screen.minibar(' ( Auto-completion aborted )')
    minibar_completer.give_up()
    completer_engine.selected = -1

def monoline_loop(editor: _Editor):
    last_insert = ''
    while True:
        
        if not editor._input_queue.qsize():
            try:
                completer_engine.update()
                all_done = True
            except:
                all_done = False
            finally:
                key_press = editor.read_stdin()
#            key_press, all_done = async_update(editor.read_stdin, completer_engine.update)
        else:
            key_press = editor.read_stdin()
            all_done = False

#        key_press = editor.read_stdin()
#        key_press, all_done = async_update(editor.read_stdin, completer_engine.update)
#        key_press, all_done = editor.read_stdin(), False
        if (key_press in completion_dict) and all_done:
            if completion_dict[key_press](editor):
                continue

        if key_press in editor.actions.insert:
            return key_press
        
        elif key_press.isprintable():
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
    editor.current_buffer.stop_selection()
    global completer_engine
    completer_engine = Completer(editor.current_buffer)
    user_input = monoline_loop(editor) 
    
    cancel_minibar = minibar(f' __ Processing command: {_escape(user_input)} __')
    
    try:
        action = dictionary[user_input]
    except KeyError:
        raise editor.MustGiveUp(f' ( Invalid command: {_escape(user_input)} )')
    
    mode = action(editor)
    cancel_minibar()
    minibar_completer.give_up()

    return mode

