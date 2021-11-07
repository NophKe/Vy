"""Helper function to deal with the linux console.
"""
from termios import *
from tty import *
from sys import stdin, stdout, stderr

IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

def stdout_no_cr():
        mode = tcgetattr(stdin)
#       mode[OFLAG] = mode[OFLAG] & ~OCRNL
#       mode[OFLAG] = mode[OFLAG] & ONOCR
#       mode[OFLAG] = mode[OFLAG] & ~ONLRET
#       mode[IFLAG] = mode[IFLAG] & ~INLCR
#       mode[IFLAG] = mode[IFLAG] & IGNCR
        mode[LFLAG] = mode[LFLAG] & ~ECHONL
        tcsetattr(stdin, TCSAFLUSH, mode)

        mode = tcgetattr(stdout)
#       mode[OFLAG] = mode[OFLAG] & ~OCRNL
#       mode[OFLAG] = mode[OFLAG] & ONOCR
#       mode[OFLAG] = mode[OFLAG] & ~ONLRET
#       mode[IFLAG] = mode[IFLAG] & ~INLCR
#       mode[IFLAG] = mode[IFLAG] & IGNCR
        mode[LFLAG] = mode[LFLAG] & ~ECHONL
        tcsetattr(stdout, TCSAFLUSH, mode)

        mode = tcgetattr(stderr)
#       mode[OFLAG] = mode[OFLAG] & ~OCRNL
#       mode[OFLAG] = mode[OFLAG] & ONOCR
#       mode[OFLAG] = mode[OFLAG] & ~ONLRET
#       mode[IFLAG] = mode[IFLAG] & ~INLCR
#       mode[IFLAG] = mode[IFLAG] & IGNCR
        mode[LFLAG] = mode[LFLAG] & ~ECHONL
        tcsetattr(stderr, TCSAFLUSH, mode)

class stdin_no_echo_nl:
    """use like:
    with stdin_no_echo():
        uifunction()
    """
    def __enter__(self):
        mode = tcgetattr(stdin)
        self.mode = mode[:]
        mode[LFLAG] = mode[LFLAG] & ~ICANON
        mode[LFLAG] = mode[LFLAG] & ~ECHONL
        mode[LFLAG] = mode[LFLAG] & ECHO
        tcsetattr(stdin, TCSAFLUSH, mode)
    def __exit__(self, *args):
        tcsetattr(stdin, TCSAFLUSH, self.mode)

class stdin_no_echo:
    """use like:
    with stdin_no_echo():
        uifunction()
    """
    def __enter__(self):
        self.mode = tcgetattr(stdin)
        setnoecho(stdin)
    def __exit__(self, *args):
        tcsetattr(stdin, TCSAFLUSH, self.mode)

def setnoecho(fd, when=TCSAFLUSH):
    mode = tcgetattr(fd)
    mode[LFLAG] = mode[LFLAG] & ~ECHO
    tcsetattr(fd, when, mode)

def setnonblocking(fd, when=TCSAFLUSH):
    mode = tcgetattr(fd)
    mode[CC][VMIN] = 0
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)

def get_a_key():
    """This function reads an only one key from the keyboard and returns it.
    if this key is the <ESCAPE> key however, it checks if there are things
    left to read in the stdin buffer. This way we read one char at a time,
    but we steal collapse escape sequences."""
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

def visit_stdin(vtime=0):
    old_mode = tcgetattr(stdin)

    mode = old_mode[:]
    mode[IFLAG] = mode[IFLAG] & ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON)
    mode[OFLAG] = mode[OFLAG] & ~(OPOST)
    mode[CFLAG] = mode[CFLAG] & ~(CSIZE | PARENB)
    mode[CFLAG] = mode[CFLAG] | CS8
    mode[LFLAG] = mode[LFLAG] & ~(ECHO | ICANON | IEXTEN | ISIG)
    mode[LFLAG] = mode[LFLAG] & ECHO
    mode[CC][VMIN] = 0
    mode[CC][VTIME] = 1
    tcsetattr(stdin, TCSAFLUSH, mode)
    
    esc_mode = old_mode[:]
    esc_mode[CC][VTIME] = 0

    while True:
        ret = stdin.read(1)
        if not ret:
            yield None
        elif ret == '\x1b':
            tcsetattr(stdin, TCSAFLUSH, esc_mode)
            esc_seq = stdin.read()
            if esc_seq:
                ret += esc_seq
            tcsetattr(stdin, TCSAFLUSH, old_mode)
            yield ret
