from .helpers import CommandCompleter

def loop(editor):
    curbuf = editor.current_buffer
    editor.screen.minibar('')
    editor.screen.bottom()
    try:
        with CommandCompleter("search_backward_history"):
            needle = input('?')
    except (KeyboardInterrupt, EOFError):
        return 'normal'

    if not needle:
        needle = editor.registr['/']
    else:
        editor.registr['/'] = needle
    if not needle:
        return 'normal'
    offset = curbuf._string.find(needle, curbuf.cursor+1)
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
