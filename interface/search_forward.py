from vy.interface.helpers import Completer

def init(editor):
    global readline
    readline = Completer('search_forward_history', '/', editor)

def loop(editor):
    try:
        user_input = readline()
    except KeyboardInterrupt:
        return 'normal'

    if user_input:
        editor.registr['/'] = user_input
    
    with editor.current_buffer:
        editor.actions.normal('n')
        editor.actions.normal('zz')
        editor.screen.recenter()
    return 'normal'
    
