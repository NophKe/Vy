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
from termios import tcgetattr, tcsetattr

#### All Flags above could have been imported
##   from the termios module, but here is an oportunity to document
##   what those actualy do on a modern linux machine

### tcsetattr() and tcsetattr() scheduling policy
#
TCSANOW = 0    # to change immediately
TCSADRAIN = 1  # to change after transmitting all queued output
TCSAFLUSH = 2  #  after TCSADRAIN and discarding all queued input.

## 
#
ISIG = 1
BRKINT = 2
INPCK = 16
ISTRIP = 32
ICRNL = 256
IXON = 1024
IEXTEN = 32768

# CC options
VTIME = 5
VMIN = 6

# OFLAG options
OPOST = 1

# LFLAG options
ICANON = 2
ECHO = 8    

# CFLAG options
CSIZE = 48
PARENB = 256
CS8 = 48

# FLAGS
IFLAG = 0  # /* input modes */
OFLAG = 1  # /* output modes */
CFLAG = 2  # /* control modes */
LFLAG = 3  # /* local modes */
ISPEED = 4 #                 input speed ?
OSPEED = 5 #                 output speed ?
CC = 6     # /* special characters */

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
            select([buffer],[],[], 0.1)
            ret = buffer.read(1)
            if ret != b'\x1b':
                while True:
                    try:
                        yield ret.decode('utf-8')
                        break
                    except UnicodeDecodeError:
                        ret += buffer.read(1)
            
            else:
                next_one = buffer.read(1)
                if next_one != b'[':
                    yield (ret+next_one).decode('ascii')
                else:
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
                        button  = ord(buffer.read(1)) - 32 # 32 == ord(ascii(' '))
                        coord_x = str(ord(buffer.read(1)) - 32) # 32 == ord(ascii(' '))
                        coord_y = str(ord(buffer.read(1)) - 32) # 32 == ord(ascii(' '))
                        if button == 64:
                            yield '\x1b[A'
                        elif button == 65:
                            yield '\x1b[B'
                        else:
                            if button == 0:
                                yield f'vy:mouse:left'
                            elif button == 1:
                                yield 'vy:mouse:middle'
                            elif button == 2:
                                yield 'vy:mouse:right'
                            else:
                                yield f'vy:mouse:{button=}'
                                continue # discard coordonates
                            yield coord_x
                            yield coord_y
                    else:
                        yield ret.decode('ascii')
                
            
    finally:
        tcsetattr(stdin, TCSAFLUSH, old_mode)

def getch_noblock():
    file = open("/home/nono/LOG_console.txt", 'a')
    for key_press in getch_noblock_base():
        if key_press:
            file.write(f'pressed: {key_press}\n')
            file.flush()
        yield key_press

#getch_noblock = getch_noblock_base
