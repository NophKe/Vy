from .helpers import CommandCompleter

def make_word_list(string):
    from re import split
    return set(split(r'[ :,()\[\]]|$', string))
        
def loop(editor):
    curbuf = editor.current_buffer

    editor.screen.minibar('')
    editor.screen.bottom()
    with CommandCompleter('search_forward_history'):
        try:
            user_input = input('/')
        except (KeyboardInterrupt, EOFError):
            return 'normal'

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

