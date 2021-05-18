"""
This file can be used as a module, defining escape sequences that ansi
vt100 and «de facto» standard uses for most common special keys.

You may also use this file to check the escape sequence your computer uses
by calling it from command line ('python keys.py'). In this case it will
produce valid python statements as below.
"""

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

#Control

C_A = '\x01'
C_B = '\x02'
C_C = '\x03'
C_D = '\x04'
C_E = '\x05'
C_F = '\x06'
C_G = '\x07'
C_H = '\x08'
C_I = '\x09'
C_J = '\x0a'
C_K = '\x0b'
C_L = '\x0c'
C_M = '\x0d'
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

#Alt + function key
A_f4 = '\x1b\x5b\x31\x3b\x33\x53'

if __name__ == '__main__':
    from console import get_a_key
    file_out = input('write to a file? give it a name or just type [enter] : ')
    if file_out:
        file_out = open(file_out, "w+")
    else:
        from sys import stdout as file_out

    print('hit [SPACE] to leave.')

    key_press = get_a_key()
    while (key_press  != ' '):
        name = input('give this key a name:')
        file_out.write(f"{name} = '")
        for each in key_press:
            file_out.write('\\')
            seq = str(hex(ord(each)))[2:]
            if len(seq) == 1:
                file_out.write('x0' + seq)
            else:
                file_out.write('x' + seq)
        file_out.write("'\n")
        file_out.flush()
        key_press = get_a_key()
