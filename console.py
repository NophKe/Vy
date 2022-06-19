"""Helper function to deal with the linux console.
"""
from termios import *
from tty import *
from sys import stdin

IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

#class save_stdin_state:
    #__slots__ = 'mode'
    #def __enter__(self):
        #self.mode = tcgetattr(stdin)
    #def __exit__(self, *args):
        #tcsetattr(stdin, TCSAFLUSH, self.mode)

#def setnoecho(fd, when=TCSAFLUSH):
    #mode = tcgetattr(fd)
    #mode[LFLAG] = mode[LFLAG] & ~ECHO
    #tcsetattr(fd, when, mode)

def setnonblocking(fd, when=TCSAFLUSH):
    mode = tcgetattr(fd)
    mode[CC][VMIN] = 0
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)

def get_a_key():
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

def visit_stdin():
    """
    This is the couter-part of the get_a_key() function also defined in the
    current module. visit_stdin() returns a generator yielding key strokes.
    """
    old_mode = tcgetattr(stdin)

    mode = old_mode[:]
    mode[IFLAG] = mode[IFLAG] & ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON)
    mode[OFLAG] = mode[OFLAG] & ~(OPOST)
    mode[CFLAG] = mode[CFLAG] & ~(CSIZE | PARENB)
    mode[CFLAG] = mode[CFLAG] | CS8
    mode[LFLAG] = mode[LFLAG] & ~(ECHO | ICANON | IEXTEN | ISIG)
    mode[CC][VMIN] = 0
    mode[CC][VTIME] = 1
    
    esc_mode = mode[:]
    esc_mode[CC][VTIME] = 0

    try:
        tcsetattr(stdin, TCSAFLUSH, mode)
        while True:
            ret = stdin.read(1)
            if ret == '\x1b':
                tcsetattr(stdin, TCSAFLUSH, esc_mode)
                esc_seq = stdin.read(1) # not sure if this part is useful
                while esc_seq:          # maybe just act as in get_a_key()
                    if esc_seq == '\x1b':
                        yield ret
                        ret = ''
                    ret += esc_seq
                    esc_seq = stdin.read(1)
                tcsetattr(stdin, TCSAFLUSH, mode)
            yield ret
    finally:
        tcsetattr(stdin, TCSAFLUSH, old_mode)

def visit_stdin():
    while True:
        yield get_a_key()
