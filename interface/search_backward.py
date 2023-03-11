from .helpers import Completer
from vy.actions import do_zz

def init(editor):
    global readline
    readline = Completer('search_backward_history', '?', editor)
        
def loop(editor):
    curbuf = editor.current_buffer
    current_offset = curbuf.cursor
    needle = readline()

    if not needle:
        needle = editor.registr['/']
    else:
        editor.registr['/'] = needle
    if not needle:
        return 'normal'

    offset = curbuf.string.rfind(needle, 0, curbuf.cursor)

    if offset == current_offset:
        offset = curbuf.string.rfind(needle, 0, curbuf.cursor - 1)

    if offset == -1:
        editor.screen.minibar('String not found: back to the end.')
        offset = curbuf._string.rfind(needle)

    if offset == -1:
        editor.screen.minibar('String not found!')
        return 'normal'

    do_zz(editor)
    curbuf.cursor = offset
    return 'normal'
