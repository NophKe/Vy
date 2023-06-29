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
from termios import *
from sys import stdin

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

def getch_noblock():
    """
    This is the couter-part of the getch() function from the same
    module.  getch_noblock() returns a generator yielding key strokes or
    None every 0.1 seconds
    """
    old_mode = tcgetattr(stdin)
    try:
        setraw(stdin)           # First,
        setnonblocking(stdin)   # Second, 
        while True:
            select([stdin],[],[], 0.1)   # wait for a character 0.1 seconds
            ret = stdin.read(1)          # rely on assertion .read(1) will not
                                         # break multi-bytes characters
            if ret == '\x1b':
                esc_seq = stdin.read(1) 
                while esc_seq:
                    # While there are things left in the buffer this sould be 
                    # considered as part of the escape sequence, but if we read 
                    # <ESC> again this mean the user is holding the key. 
                    # There is a subtil bug! if user holds a special key and
                    # presses a normal key very quickly.... What can we do ?
                    if esc_seq == '\x1b':
                        yield ret
                        ret = ''
                    ret += esc_seq
                    esc_seq = stdin.read(1)
            yield ret
    finally:
        tcsetattr(stdin, TCSAFLUSH, old_mode)
