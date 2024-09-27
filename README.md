Vy
===

What is Vy?
-----------

Lets just say that I wanted to write a little "Ed" clone (the classical
unix "ed", line oriented text editor), but I felt frustrated when I
discovered there was no getch() function in the Python standard library.
And this brought me into some diving in the implementation the linux
console.

getch() and the stdin problem
-----------------

For obvious unicode and encodings related issues, in python the unicode
string rules them all... This means one should never rely on
sys.stdin.read(1) to read an only one byte char, as this will need to
read bytes until the whole sequence matches a valid code-point.  Do you
know how many bytes are hidden in this ? 

Moreover some characters like that stupid up-arrow on your keyboard...
are historically mapped to an escape sequence consisting of multiple
bytes.  When '\x1b' is received by stdin is it the esc key or is there
more data inthe buffer?

1. There is nothing! The user pressed the esc key.
2. There is! '\x5b\x44' this means the user pressed the up-arrow.

Yes, I know... Easy!

What would happen a little delay takes place before '\x5b\x44' arrives?

There is nothing! The user pressed the esc key.
New data incomming... '\x5b\x44'... looks like this is valid ascii/utf-8 string.
This means the user pressed the characters '[A'.

Use blocking/ non-blocking strategies, use tty rates and tricks and get it right!

Of course... Easy!

Mouse events?  Mapped to escape sequences too!  And you need to read a
few more bytes to know the location on the creen where the event took place.

 and are read from stdin.

stdin 

Vy is a **light** python implementation of the Vi text editor.  It has
no external dependency outside standard lib.  But it can use the
Pygments library (if present) for syntax highlighting, and Jedi (if
present) for things like auto-completion, python introspection, renaming
variable across a python package <3... related operations.  Vy aims to
stay less than 10_000 lines (including doc) and run on any modern
python+linux machine.

At the time of this writing, it it working enough so that I would prefer
it to the traditionnal vi, and the ability to have the python repl
inside the editor would make me prefer it over vim for python oriented
stuff where you would like to evaluate expressions in real time.

Not a clone and legacy-free
---------------------------

First It is meant to be legacy-free.  Even if it might feel the same
while using it, some quirks or the vi/vim grammar are to be eliminated.
Indeed Vy tries to provide a classic Vi-like interface that aims to be
easy to extend through the python programming interface.  It does not
provide anything like VimScript but tries to expose its internals in a
«pythonic» way.

POSIX is to be forgotten, unless to create a compatibility layer... No
termcap, no terminfo is needed anymore.  I claim nobody execute python
on a VT100 terminal ! IO speed used to be a problem.  Refreshing a tty
screen required data saving not to waste the physical dial-up line.

Nowaday, with no other information than the size of the terminal screen,
it is easily feasible to send a whole screen several times a second !

Vym will never try to handle weird terminals.  It makes minimal terminal
manipulation, and will keep to very basic vt100/ANSI/«de facto»
standard.

It imports very few from stdlib, doesn't use readline, doesn't use
curses, nor any other library for terminal manipulation.  The goal is to
keep the code as «low level» and «de-pendency free» as possible.

It **must** be self-documenting, and the application API must be
discoverable.

Vym will will never be better at encodings than vanilla python allready
is, and will never handle binary files.

Implemented Features
--------------------

* Syntax highlighted through Pygments library (optionnal)
* Auto-completion through Jedi library (optionnal)
* Linear undo/redo
* Copy / paste and Registers
* Macros
* Expandtabs
* Windows with vertical splits
* Most basic motions ( W w e E $ gg G b _ 0 h j k l )
* Most basic editing stuff...


Q Mode
------

Fed up hiting the Q key in vim?  In Vy this leads you to a python unique
prompt where you can enter any valid python expression or statement or
code block.

The Vy editor is accessible by the «Editor» variable.
    
    >>> Editor.screen.vertical_split()


Python Mode
-----------
The repl inside the editor.
```py
    :python
            You are now in a python repl.
            You can access Vy by the «Editor» variable.

    >>> from time import asctime
	>>> from vy.keys import C_T
	>>> 
	>>> def insert_time_in_buffer(editor, **kwargs):
	... 	"""
	...		Inserts a timestamp at the cursor position
	...		"""
    ... 	editor.current_buffer.insert(asctime())
	...
	>>> Editor.action.normal[C_T] = insert_time_in_buffer
```

from vy.filetypes.textfile import TextFile
------------------------------------------

```py
    >>> buffer = TextFile('/etc/hosts')

    >>> buffer.read()
    '255.0.0.1  localhost \n'
    
    >>> buffer.string = ''
    >>> buffer.read()
    ''

    >>> buffer.write('127.0.0.1  localhost \n')

    >>> buffer.undo()
    >>> buffer.redo()
    
    >>> buffer.unsaved
    True

    >>> buffer.save()
```
