"""
    ***********************************
    ****    The Console Helpers    ****
    ***********************************

The 'vy.console' module contains helper functions to deal with the linux
console.

It defines the getch() blocking function to read a single keypress.  And
getch_noblock() is used by Editor.input_thread to feed the input_queue
and Editor.read_stdin().

setnonblocking() puts the terminal in non blocking mode allowing to
return immediatly with an empty string from a call to stdin.read(). This
allow the thread that called the read to remain joinable after a given
timeout.

The setraw() function is a copy from the cpython standard library.  As
setnonblocking needed the same imports as the tty module that defines
it.  And setraw being a dependency of getch, copying 10 lines of code
prevented several call to the import machinery.
"""

from select import select
from sys import stdin
from termios import (TCSAFLUSH, TCSANOW, tcgetattr, tcsetattr, VMIN, VTIME,
                        BRKINT, ICRNL, INPCK, ISTRIP, IXON, OPOST, CSIZE,
                        PARENB, ECHO, ICANON, IEXTEN, ISIG, CS8)
IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

def setraw(fd, when=TCSAFLUSH):
    """
    Put terminal into a raw mode.
    """
    mode = tcgetattr(fd)
    mode[IFLAG] = mode[IFLAG] & ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON)
    mode[OFLAG] = mode[OFLAG] & ~(OPOST)
    mode[CFLAG] = mode[CFLAG] & ~(CSIZE | PARENB)
    mode[CFLAG] = mode[CFLAG] | CS8
    mode[LFLAG] = mode[LFLAG] & ~(ECHO | ICANON | IEXTEN | ISIG)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)

def setnonblocking(fd, when=TCSANOW):
    """
    Put terminal into a non-blocking mode.
    """
    mode = tcgetattr(fd)
    mode[CC][VMIN] = 0
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)

def getch():
    """
    This function reads an only one key from the keyboard and returns
    it.  if this key is the <ESCAPE> key however, it checks if there are
    things left to read in the stdin buffer.  This way we read one char
    at a time, but we steal collapse escape sequences.
    """
    old_mode = tcgetattr(stdin)
    setraw(stdin)
    rv = stdin.read(1)
    if rv == '\x1b':
        setnonblocking(stdin)
        esc_seq = stdin.read()
        if esc_seq:
            rv += esc_seq
    tcsetattr(stdin, TCSADRAIN, old_mode)
    return rv
        
def getch_noblock_base():
    """
    This is the couter-part of the getch() function from the same
    module.  getch_noblock() returns a generator yielding key strokes or
    None every 0.1 seconds
    """
    old_mode = tcgetattr(stdin)
    buffer = stdin.buffer
    try:
        setraw(stdin)           # First,
        setnonblocking(stdin)   # Second, 
        while True:
            select([buffer],[],[], 0.1)          # wait for a character 0.1 seconds
            ret = buffer.read(1)          # rely on assertion .read(1) will not
            if ret == b'\x1b':
                next_one = buffer.read(1)
                if next_one == b'[':
                    ret = ret + next_one + buffer.read(1)
                    
                    while ret[-1] not in range(0x40,0x7e+1):
                        ret += buffer.read(1) 
                        
                    if ret == b'\x1b[200~':
                        ret = buffer.read(1)
                        while not ret.endswith(b'\x1b[201~'):
                            ret += buffer.read(1)
                        ret = ret.removesuffix(b'\x1b[201~')
                        yield 'vy:paste'
                        yield ret.replace(b'\r', b'\n').decode('utf-8')
                        
                    elif ret == b'\x1b[M':
                        button = str(ord(buffer.read(1)) - 32) # 32 == ord(ascii(' '))
                        coord_x = str(ord(buffer.read(1)) - 32) # 32 == ord(ascii(' '))
                        coord_y = str(ord(buffer.read(1)) - 32) # 32 == ord(ascii(' '))
                        if button == '64':
                            yield '\x1b[A'
                        elif button == '65':
                            yield '\x1b[B'
                        else:
                            yield 'vy:mouse'
                            yield button
                            yield coord_x
                            yield coord_y
                    else:
                        yield ret.decode('ascii')
                
                else:
                    yield (ret+next_one).decode('ascii')
                
            else:
                while True:
                    try:
                        yield ret.decode('utf-8')
                        break
                    except UnicodeDecodeError:
                        ret += buffer.read(1)
            
    finally:
        tcsetattr(stdin, TCSAFLUSH, old_mode)

def getch_noblock():
    file = open("/home/nono/LOG_console.txt", 'a')
    for key_press in getch_noblock_base():
        if key_press:
            file.write(f'{key_press = }\n')
            file.flush()
        yield key_press

getch_noblock = getch_noblock_base
