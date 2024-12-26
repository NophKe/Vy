import readline
from vy.console import getch

print(' press [ i ] to inspect')
print(' press [ t ] to test')

print(' press any other key to create a key mapping')

key = getch()
if key == 'i':
    from pprint import pp
    pp(_reprs)
elif key == 't':
#        from vy.editor import _Editor
#        ed = _Editor()
#        for key in ed.actions.visual:
#            print(f'{repr(key) = :30} {_escape(key) =}')
#        for key in ed.actions.normal:
#            print(f'{repr(key) = :30} {_escape(key) =}')
#        for key in ed.actions.insert:
#            print(f'{repr(key) = :30} {_escape(key) =}')
#        for key in ed.actions.command:
#            print(f'{repr(key) = :30} {_escape(key) =}')
    pass
else:
    file_out = input('write to a file? give it a name or just type [enter] : ')
    if file_out:
        file_out = open(file_out, "w+")
    else:
        from sys import stdout as file_out

    print('hit [SPACE] to leave or enter new keypress')
    key_press = getch()

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
        print('hit [SPACE] to leave or enter new keypress')
        key_press = getch()
