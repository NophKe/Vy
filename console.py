"""
Helper functions to deal with the linux console.
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
    """Put terminal into a raw mode."""
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
    mode = tcgetattr(fd)
    mode[CC][VMIN] = 0
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)

def getch():
    """
    This function reads an only one key from the keyboard and returns it.
    if this key is the <ESCAPE> key however, it checks if there are things
    left to read in the stdin buffer. This way we read one char at a time,
    but we steal collapse escape sequences.
    """
    mode = tcgetattr(stdin)
    setraw(stdin)
    rv = stdin.read(1)
    if rv == '\x1b':
        setnonblocking(stdin)
        esc_seq = stdin.read()
        if esc_seq:
            rv += esc_seq
    tcsetattr(stdin, TCSAFLUSH, mode)
    return rv

def getch_noblock():
    """
    This is the couter-part of the getch() function also defined in the
    current module. getch_noblock() returns a generator yielding key strokes
    or None every 0.1 seconds
    """
    old_mode = tcgetattr(stdin)
    try:
        setraw(stdin)           # First,
        setnonblocking(stdin)   # Second, 
        while True:
            select([stdin],[],[], 0.1)       # wait for a character
            # rely on .read(1) not splitting multi-bytes chars
            ret = stdin.read(1)
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
