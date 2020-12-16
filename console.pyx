from termios import *
from tty import *
from sys import stdin, stdout, stderr

DEF IFLAG = 0
DEF OFLAG = 1
DEF CFLAG = 2
DEF LFLAG = 3
DEF ISPEED = 4
DEF OSPEED = 5
DEF CC = 6

cpdef setnoecho(fd, when=TCSAFLUSH):
    mode = tcgetattr(fd)
    mode[LFLAG] = mode[LFLAG] & ~ECHO
    tcsetattr(fd, when, mode)

cpdef setnonblocking(fd, when=TCSAFLUSH):
    mode = tcgetattr(fd)
    mode[CC][VMIN] = 0
    mode[CC][VTIME] = 0
    tcsetattr(fd, when, mode)

cpdef str get_a_key():
    cdef str rv
    cdef list mode
    cdef str esc_seq

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
