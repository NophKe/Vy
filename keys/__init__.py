"""
This file can be used as a module, defining escape sequences that ansi
vt100 and «de facto» standard uses for most common special keys.

You may also use this file to check the escape sequence your computer uses
by calling it from command line ('python keys.py'). In this case it will
produce valid python statements as below.
"""
from .alt_keys import *
from .function_keys import *

# Backspace combinations
M_bs = '\x88'
C_M_bs = '\xff'
C_bs = '\x7f'

# Control + misc
A_esc = M_esc = '\x9b'

# TAB combinations
M_tab = '\x89'
C_tab = '\x09'
S_tab = '\x1b\x5b\x5a'

# Shift + Arrow
S_right = '\x1b\x5b\x31\x3b\x32\x43'
S_left = '\x1b\x5b\x31\x3b\x32\x44'
S_up = '\x1b\x5b\x31\x3b\x32\x41'
S_down = '\x1b\x5b\x31\x3b\x32\x42'

# Control + Arrow
C_right = '\x1b\x5b\x31\x3b\x35\x43'
C_left = '\x1b\x5b\x31\x3b\x35\x44'
C_up = '\x1b\x5b\x31\x3b\x35\x41'
C_down = '\x1b\x5b\x31\x3b\x35\x42'

# Arrows
right = '\x1b\x5b\x43'
left = '\x1b\x5b\x44'
up = '\x1b\x5b\x41'
down = '\x1b\x5b\x42'

# Buffer moves
page_up = '\x1b\x5b\x35\x7e'
page_down = '\x1b\x5b\x36\x7e'
end = '\x1b\x5b\x46'
beginning = '\x1b\x5b\x48'

#change mode
insert = '\x1b\x5b\x32\x7e'
escape = '\x1b'

#text editing
suppr = '\x1b\x5b\x33\x7e'
space = '\x20'   # needs a hack in helpers.py to work

# Control keys and alias
C_arobase = '\x00'
C_A = '\x01'
C_B = '\x02'
C_C = '\x03'
C_D = '\x04'
C_E = '\x05'
C_F = '\x06'
C_G = '\x07'
C_H = backspace = BS = '\x08'
linux_backpace = '\x7f'
C_I = '\x09'
C_J = '\x0a'
C_K = '\x0b'
C_L = '\x0c'
C_M = CR = '\x0d'
C_N = '\x0e'
C_O = '\x0f'
C_P = '\x10'
C_Q = '\x11'
C_R = '\x12'
C_S = '\x13'
C_T = '\x14'
C_U = '\x15'
C_V = '\x16'
C_W = '\x17'
C_X = '\x18'
C_Y = '\x19'
C_Z = '\x1a'
C_lbra = '\x1b'
C_antislash = '\x1c'
C_rbra = '\x1d'
C_caret = '\x5e' # I double checked it but it still doesn't look right
C_underscore = '\x1f'


#Alt + function key
A_f4 = '\x1b\x5b\x31\x3b\x33\x53'


_reprs = {key: value for (value, key) in vars().items()
                if isinstance(key, str) 
                if not value.startswith('_')}

def _escape(text):
    """
    Returns a string with escaped version of non-printable chars
    in a vim fashion (like <CR> for NewLine and <C_W> for [Ctrl+W]
    """
    final = ''
    evaluing = ''
    char = ''
    for char in  text:
        if evaluing:
            if any( [item.startswith(evaluing + char) for item in _reprs]):
                evaluing += char
                continue
            try:
                final += ('<' + _reprs[evaluing] + '>').replace('_','-')
            except KeyError:
                return repr(evaluing)
                
            if char.isprintable():
                evaluing = ''
                final += char.replace('_','-')
                continue
            evaluing = char
            continue
        if any( [item.startswith(char) for item in _reprs]): 
            evaluing += char
            continue
        if char.isprintable():
            assert not char.isspace()
            final += char
    if evaluing:
        try:
            final += ('<' + _reprs[evaluing] + '>').replace('_','-')
        except KeyError:
            return repr(evaluing)

    assert final.isprintable()
    assert not any(forbiden in final for forbiden in '\n\t\x1b')
    return final

def _build_table():
    global _reprs
    return [(repr(key), _escape(key)) for key in _reprs.values()]
