from vy.interface.helpers import Completer
from vy.editor import _Editor

def init(editor):
    global readline
    readline = Completer('search_forward_history', '/', editor)

def loop(editor: _Editor):
    try:
        user_input = readline()
    except KeyboardInterrupt:
        return 'normal'

    if user_input:
        editor.registr['/'] = user_input
    
        editor.actions.normal('n')
#        from time import sleep
        editor.actions.normal('zz')
        
    return 'normal'
    
