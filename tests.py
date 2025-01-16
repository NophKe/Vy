bad_string = "H̹̙̦̮͉̩̗̗ͧ̇̏̊̾Eͨ͆͒̆ͮ̃͏̷̮̣̫̤̣Cͯ̂͐͏̨̛͔̦̟͈̻O̜͎͍͙͚̬̝̣̽ͮ͐͗̀ͤ̍̀͢M̴̡̲̭͍͇̼̟̯̦̉̒͠Ḛ̛̙̞̪̗ͥͤͩ̾͑̔͐ͅṮ̴̷̷̗̼͍̿̿̓̽͐H̙̙̔̄͜"
#print(f'{len(bad_string) =}')

from pathlib import Path
from time import time, asctime
from vy.filetypes.textfile import TextFile
from vy.filetypes.basefile import BaseFile
from sys import stdout as _stdout
from sys import argv

_bench_file = open("/home/nono/vy_benchmark.txt", mode="a")

def _print(*args):
    print(*args, file=_bench_file)
    print(*args)

def _insert_header():
    _print(f'**************************** {asctime()}            ********************************')


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
    _print(f'bench_basefile:\n\t\t took {round(time() - start, 3)} seconds.')

def bench_insert_str():
    start = time()
    for _ in range(100):
        file.cursor = _
        file._string_insert('hi')
        len(file.string)
        len(file.splited_lines)
        file.cursor_lin_col
    _print(f'bench_insert_string:\n\t\t took {round(time() - start, 3)} seconds.')
    
def bench_insert_list():
    start = time()
    for _ in range(100):
        file.cursor = _
        file._list_insert('hi')
        len(file.string)
        len(file.splited_lines)
        file.cursor_lin_col
    _print(f'bench_insert_list:\n\t\t took {round(time() - start, 3)} seconds.')

def bench_lexed_lines():
    File = TextFile(path="/home/nono/test_me.py")
    counter = 0
    start = time()
    max_lin = File.number_of_lin
    
    for i in range(100):
        saved = File.string
        File._lexed_cache.clear()
        File.string = "#pragma\n"
        File.string = saved
        try:
            file.get_raw_screen(max_lin-i*10, max_lin)
            File.get_raw_screen(0,max_lin)
        except RuntimeError:
            counter += 1
            
    _print(f'bench_get_lexed_lines:\n\t\t took {round(time() - start, 3)} seconds.')
    _print(f'failed {counter} times')

path = Path('/home/nono/vy/oldies.c')
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
    _print(f'bench_grab_lock:\n\t\t took {round(time() - start, 3)} seconds.')

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

def bench_expandtabs():
    from vy.screen import expandtabs_numbered
    tab_size = 4
    max_col = 16
    text = '0123\x1b[31;45m4567\x1b[31;42;2m89ABCDEF\n' * 50
    on_lin = 1
    num_len = 1
    
    start = time()
    for idx in range(100):
        cursor_lin = 1
        cursor_col = idx * 2
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
        visual = (6, 11+idx)
        expandtabs_numbered(tab_size, max_col, text, on_lin, cursor_lin, cursor_col, num_len, visual)    
    _print(f'bench_expandtabs:\n\t\t took {round(time() - start, 3)} seconds.')


if __name__ == '__main__':
    _insert_header()

    if argv[1:]:
        start = time()
        for test in argv[1:]:
            globals()[test]()
        _print(f'Whole Test Suite:\n\t\t took {round(time() - start, 3)} seconds.')
        
    else:
        start = time()
        for test in dir():
            if test.startswith('bench') or test.startswith('test'):
                globals()[test]()
        _print(f'Whole Test Suite:\n\t\t took {round(time() - start, 3)} seconds.')


