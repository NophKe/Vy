from .helpers import Completer
from vy.actions import do_zz

def init(editor):
    global readline
    readline = Completer('search_backward_history', '?', editor)
    center_screen = editor.actions.normal[
        
def loop(editor):
    curbuf = editor.current_buffer
    needle = readline()

    if not needle:
        needle = editor.registr['/']
    else:
        editor.registr['/'] = needle
    if not needle:
        return 'normal'

    offset = curbuf.string.find(needle, curbuf.cursor+1)
    if offset == -1:
        editor.screen.minibar('String not found: back to the top.')
        offset = curbuf._string.find(needle)
        if offset == -1:
            editor.screen.minibar('String not found!')
            return 'normal'
        curbuf.cursor = offset
        do_zz(editor)
    else:
        do_zz(editor)
        curbuf.cursor = offset + 1
        return 'normal'
