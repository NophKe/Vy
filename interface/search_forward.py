from vy.actions import do_zz, do_normal_n
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
    
    do_normal_n(editor)
    do_zz(editor)
    
    return 'normal'
    
