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
    print(f'bench_basefile:\t\t took {round(time() - start, 3)} seconds.')

path ='/home/nono/test.c'
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
    print(f'bench_grab_lock:\t\t took {round(time() - start, 3)} seconds.')

def bench_textfile():
    global file
    start = time()
    for t in range(5):
        file.insert('#pragma Nono\n')
        while True:
            try:
                file.get_raw_screen(10_000, 11_000)
                #file.get_raw_screen(30_000, 31_000)
                #file.get_raw_screen(33_500, 34_000)
            except RuntimeError:
                sleep(0.01)
                continue
            break
    print(f'bench_textfile:\t\t took {round(time() - start, 3)} seconds.')

# This class should one day replace the command class
class CMD:
    def __new__(cls, *args, **kwargs):
        cls.seen = set()
        super.__new__(cls, *args, **kwargs)
    def __init_subclass__(cls, /, alias_dict, **kwargs):
        self.alias_dict = alias_dict
        super().__init_subclass__(cls, **kwargs)
    def __init__(self, header, mode_prefix):
        self.header = self.v_header % (v_alias[0] ,
                                    ' '.join(_escape(item) for item in v_alias).ljust(60))
    def update_func(self, alias, func):
        for item in alias.split(' '):
            self.alias_dict[alias] = func
        header = ''
        if func.__doc__:
            func.__doc__ = self.header + '\n' + func.__doc__ + '\n'
    def __call__(self, alias):
        return lambda func : self.update_func(alias, func)

if __name__ == '__main__':
    start = time()
    for test in dir():
        if test.startswith('bench') or test.startswith('test'):
            globals()[test]()
    print(f'Whole Test Suite:\t took {round(time() - start, 3)} seconds.')
