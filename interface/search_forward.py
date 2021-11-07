import readline
from pathlib import Path

class CommandModeCompleter:
    def __enter__(self):
        self.histfile = Path("~/.vym/search_forward_history").expanduser()
        if not self.histfile.exists():
            self.histfile.touch()
        self._old_complete = readline.get_completer() 

        readline.set_completer(lambda txt, state: None)
        readline.clear_history()
        readline.set_history_length(1000)
        readline.read_history_file(self.histfile)
        readline.parse_and_bind('tab: complete')
    
    def __exit__(self, *args, **kwargs):
        readline.write_history_file(self.histfile)
        readline.set_completer(self._old_complete)

def make_word_list(string):
    from re import split
    return set(split(r'[ :,()\[\]]|$', string))
        
def loop(editor):
    curbuf = editor.current_buffer

    editor.screen.minibar('')
    editor.screen.bottom()
    with CommandModeCompleter():
        try:
            user_input = input('/')
        except (KeyboardInterrupt, EOFError):
            return 'normal'

        if not user_input:
            user_input = editor.register['/']
        else:
            editor.register['/'] = user_input
        if not user_input:
            return 'normal'

        offset = curbuf.string.find(user_input, curbuf.cursor)
        if offset == -1:
            editor.warning('chaine de caractere non trouvée. (recherche vers l\'avant)')
            return 'normal'
        curbuf.cursor = offset
        return 'normal'

