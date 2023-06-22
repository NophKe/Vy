bad_string = "H̹̙̦̮͉̩̗̗ͧ̇̏̊̾Eͨ͆͒̆ͮ̃͏̷̮̣̫̤̣Cͯ̂͐͏̨̛͔̦̟͈̻O̜͎͍͙͚̬̝̣̽ͮ͐͗̀ͤ̍̀͢M̴̡̲̭͍͇̼̟̯̦̉̒͠Ḛ̛̙̞̪̗ͥͤͩ̾͑̔͐ͅṮ̴̷̷̗̼͍̿̿̓̽͐H̙̙̔̄͜"
#print(f'{len(bad_string) =}')

from pathlib import Path
from time import time
from vy.filetypes.textfile import TextFile
from vy.filetypes.basefile import BaseFile

def bench_basefile():
    file_txt = Path('/home/nono/big.txt').read_text()
    file = BaseFile(path='/home/nono/big.txt',
                    init_text=file_txt,
                    )
    start = time()
    for _ in range(10):
        file.cursor += file.find_end_of_line() + 2
        file.insert('hi')
        file.backspace()
        lin, col = file.cursor_lin_col
        file.cursor_lin_col = lin+1, col+1
        file.insert('hi')
        file.suppr()
        file.move_cursor('w')
        file[file.find_first_non_blank_char_in_line()] = 'toto'
        file.current_line = ' yep !' + file.splited_lines[file.current_line_idx]
    print(f'bench_basefile:\n\t\t took {round(time() - start, 3)} seconds.')

def bench_insert_str():
    start = time()
    for _ in range(100):
        file.cursor = _
        file._string_insert('hi')
        len(file.string)
        len(file.splited_lines)
        file.cursor_lin_col
    print(f'bench_insert_string:\n\t\t took {round(time() - start, 3)} seconds.')
    
def bench_insert_list():
    start = time()
    for _ in range(100):
        file.cursor = _
        file._list_insert('hi')
        len(file.string)
        len(file.splited_lines)
        file.cursor_lin_col
    print(f'bench_insert_list:\n\t\t took {round(time() - start, 3)} seconds.')

path = Path('/home/nono/test.c')
file = open(path)
value= file.read()
file.close()
file = TextFile(init_text=value, path=path)
from time import time, sleep

def bench_grab_lock():
    global file
    start = time()
    for t in range(100):
        with file:
            pass
    print(f'bench_grab_lock:\n\t\t took {round(time() - start, 3)} seconds.')

def bench_textfile():
    global file
    start = time()
    for t in range(5):
        file.insert('#pragma Nono\n')
        while True:
            try:
                file.get_raw_screen(10_000, 11_000)
            except RuntimeError:
                sleep(0.04)
                continue
            break
    print(f'bench_textfile:\n\t\t took {round(time() - start, 3)} seconds.')

def _bench_expandtabs():
    from vy.screen import expandtabs_numbered
    tab_size = 4
    max_col = 16
    text = '0123\x1b[31;45m4567\x1b[31;42;2m89ABCDEF' * 50
    on_lin = 1
    num_len = 1
    
    start = time()
    for _ in range(100):
        cursor_lin = 1
        cursor_col = 2
        visual = (0,0)
        expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col, num_len, visual)
        cursor_lin = 1
        cursor_col = 8
        visual = (0,0)
        expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col, num_len, visual)
        cursor_lin = 1
        cursor_col = 8
        visual = (6,8)
        expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col, num_len, visual)
        cursor_lin = 1
        cursor_col = 8
        visual = (6,11)
        expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col, num_len, visual)    
    print(f'bench_expandtabs:\n\t\t took {round(time() - start, 3)} seconds.')


if __name__ == '__main__':
    start = time()
    for test in dir():
        if test.startswith('bench') or test.startswith('test'):
            globals()[test]()
    print(f'Whole Test Suite:\n\t\t took {round(time() - start, 3)} seconds.')

else:
    from vy.editor import _Editor as Editor
    ed = Editor()
    ed.edit('/home/nono/test_me.py')
    for dic in [ed.actions.command, ed.actions.insert, ed.actions.insert, ed.actions.motion, ed.actions.motion]:
        for act in dic:
            try:
                dic[act](ed)
            except BaseException as exc:
                print(exc.__cause__)
                print(act)
                print(f'{dic is ed.actions.command =}')
                print(f'{dic is ed.actions.insert =}')
                print(f'{dic is ed.actions.normal = }')
                print(f'{dic is ed.actions.motion =}')
                print(f'{dic is ed.actions.visual =}')
