from .helpers import Completer

def init(editor):
    global readline
    readline = Completer('search_backward_history', '?', editor)

def make_word_list(string):
    from re import split
    return set(split(r'[ :,()\[\]]|$', string))
        
def loop(editor):

    if not user_input:
        user_input = editor.registr['/']
    else:
        editor.registr['/'] = user_input
    if not user_input:
        return 'normal'

    offset = curbuf.string.find(user_input, curbuf.cursor)
    if offset == -1:
        editor.warning('chaine de caractere non trouvée. (recherche vers l\'avant)')
        return 'normal'
    curbuf.cursor = offset
    return 'normal'

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
