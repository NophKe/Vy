from .helpers import Completer

def init(editor):
    global readline
    readline = Completer('search_backward_history', '?', editor)
        
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
    else:
        curbuf.cursor = offset + 1
        return 'normal'
