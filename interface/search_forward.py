from vy.actions import do_zz
from vy.interface.helpers import Completer

def init(editor):
    global readline
    readline = Completer('search_forward_history', '/', editor)

def loop(editor):
    curbuf = editor.current_buffer
    current_offset = curbuf.cursor
    try:
        user_input = readline()
    except KeyboardInterrupt:
        return 'normal'

    if not user_input:
        user_input = editor.registr['/']
    else:
        editor.registr['/'] = user_input
    if not user_input:
        return 'normal'

    offset = curbuf.string.find(user_input, current_offset) 
    if offset == current_offset:
        offset = curbuf.string.find(user_input, current_offset + 1)

    if offset == -1:
        editor.screen.minibar('String not found, retrying from first line.')
        offset = curbuf._string.find(user_input)

    if offset == -1:
        editor.screen.minibar('String not found!')
        return 'normal'

    curbuf.cursor = offset
    do_zz(editor)
    return 'normal'
    
