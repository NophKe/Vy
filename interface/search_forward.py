from .helpers import Completer

def init(editor):
    global readline
    readline = Completer('search_forward_history', '/', editor)

def make_word_list(string):
    from re import split
    return set(split(r'[ :,()\[\]]|$', string))
        
def loop(editor):
    curbuf = editor.current_buffer
    user_input = readline()

    if not user_input:
        user_input = editor.registr['/']
    else:
        editor.registr['/'] = user_input
    if not user_input:
        return 'normal'

    offset = curbuf.string.find(user_input, curbuf.cursor)
    if offset == -1:
        editor.warning('chaine de caractere non trouvée. (recherche vers l\'avant)')
        offset = curbuf._string.find(user_input)
        if offset == -1:
            editor.screen.minibar('String not found!')
            return 'normal'
        curbuf.cursor = offset
    else:
        curbuf.cursor = offset + 1
        return 'normal'

