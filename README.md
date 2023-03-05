Vy
===

What is Vy?
-----------

First, Vy is an experiment.

When I first discovered Python, the first that came to my mind was:

« Woow. What smooth looking api's we can make of it... »

Aside the few serious uses I made of this language, I developped in my 
spare time a little Ed clone (the classical unix "ed", line oriented text editor).

I got frustrated when I discovered there was no easy getch() function in the 
Python standard library....This got me through some diving in the implementation 
of the linux console.

For obvious unicode and encodings related issues, one should never rely on 
sys.stdin.read(1) to read an only one character. Moreover some characters like
<CURSOR-UP> are historically mapped to an escape sequence consisting of multiple bytes.

Vy is a **light** python implementation of the Vi text editor. It has 
no external dependency outside standard lib. But it can use the Pygments
library (if present) for syntax highlighting, and Jedi (if present) for things like
auto-completion, or python introspection related operations.  It aims to stay less than
10_000 lines (including doc) and run on any modern python+linux machine.

At the time of this writing, it it working enough so that I would prefer it to the
traditionnal vi, and the ability to have the python repl inside the editor would
make me prefer it over vim for python oriented stuff where you would like to evaluate
expressions in real time.

Not a clone and legacy-free
---------------------------

First It is meant to be legacy-free. Even if it might feel the same while using it,
some quirks or the vi/vim grammar are to be eliminated. Indeed Vy tries to provide 
a classic Vi-like interface that aims to be easy to extend through the python 
programming interface. It does not provide anything like VimScript but tries to expose 
its internals in a «pythonic» way. 

POSIX is to be forgotten, unless to create a compatibility layer... No termcap,
no terminfo is needed anymore. I claim nobody execute python on a VT100 terminal !
IO speed used to be a problem. Refreshing a tty screen required data saving not to
waste the physical dial-up line.

Nowaday, with no other information than the size of the terminal screen, it is easily 
feasible to send a whole screen several times a second !

Vym will never try to handle weird terminals. It makes minimal terminal manipulation,
and will keep to very basic vt100/ANSI/«de facto» standard.

It imports very few from stdlib, doesn't use readline, doesn't use curses, nor any other
library for terminal manipulation. The goal is to keep the code as «low level» and «de-
pendency free» as possible.

It **must** be self-documenting, and the application API must be discoverable.

Vym will will never be better at encodings than vanilla python allready is, and
will never handle binary files.

Implemented Features
--------------------

* Syntax highlighted through Pygments library (optionnal)
* Auto-completion through Jedi library (optionnal)
* Linear undo/redo
* Copy / paste and Registers
* Macros (will be back soon)
* Expandtabs
* Windows with vertical splits
* Most basic motions ( W w e E $ gg G b _ 0 h j k l )
* Most basic editing stuff...


Q Mode
------

Fed up hiting the Q key in vim? In Vy this leads you to a python unique prompt
where you can enter any valid python expression or statement or code block.

The Vy editor is accessible by the «Editor» variable.
    
    >>> Editor.screen.vertical_split()


Python Mode
-----------
The repl inside the editor.

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

from vy.filetypes.textfile import TextFile
------------------------------------------

```
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
