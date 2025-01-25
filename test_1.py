r'''
>>> import vy.filetypes.textfile

>>> good_buffer = vy.filetypes.textfile.TextFile(init_text='\n')
>>> bad_buffer = vy.filetypes.textfile.TextFile()

    # A buffer is a collection of lines, so it must allways contain a trailing new line

>>> good_buffer.string
'\n'

>>> bad_buffer.string
''

>>> good_buffer.cursor = len(good_buffer)
Traceback (most recent call last):
AssertionError

>>> good_buffer.cursor = len(good_buffer) -1
>>> good_buffer.insert('hello world!\n')
>>> bad_buffer.insert('hello world!\n')
>>> bad_buffer.string
'hello world!\n'
>>> bad_buffer.string
'hello world!\n'
>>> bad_buffer.cursor
13
>>> good_buffer.cursor
13
>>> bad_buffer.cursor = len(bad_buffer) - 1
>>> good_buffer.cursor = len(good_buffer) -1
>>> good_buffer.insert('The cursor can not go beyond last character index position\n')
>>> bad_buffer.insert('No really! The cursor can not go beyond last character index position\n')
'''
import doctest

#doctest.testmod()
