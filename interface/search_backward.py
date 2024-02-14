from interface.helpers import Completer
        
def init(editor):
    global readline
    readline = Completer('search_backward_history', '?', editor)
    
def loop(editor):
    try:
        user_input = readline()
    except KeyboardInterrupt:
        return 'normal'

    if user_input:
        editor.registr['?'] = user_input
    
    editor.actions.normal('N')
    editor.actions.normal('zz')
    return 'normal'
    
    
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

    editor.actions.normal('zz')
    curbuf.cursor = offset
    return 'normal'
