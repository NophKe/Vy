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

class stdin_no_echo:
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
        rv = stdin.read(1)
        if not rv:
            return
        if rv == '\x1b':
            mode[CC][VTIME] = 0
            tcsetattr(stdin, TCSAFLUSH, mode)
            esc_seq = stdin.read()
            if esc_seq:
                rv += esc_seq
        tcsetattr(stdin, TCSAFLUSH, old_mode)
        return rv
