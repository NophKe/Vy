Vy
===

What is Vy?
-----------

Vy is a **light** python implementation of the Vi text editor. It has 
no external dependency outside standard lib. But it can use the Pygments
library (if present) for syntax highlighting.  It aims to stay less than 5000
lines (including doc) and run on any modern python machine.

It tries to provide a classic Vi-like interface that aims to be easy to
extend through the python programming interface. It does not provide anything 
like VimScript but tries to expose its internals in a «pythonic» way. 

This is not supposed to be a clone of Vim or Vi. It is meant to be legacy-free.
Even if it might feel the same while using it, some quirks or the vi/vim grammar
are to be eliminated.

It must be self-documenting, and the application API mus be discoverable.

Vym will will never be better at encodings than vanilla python allready is, and
will never handle binary files.

Vym will never try to handle weird terminals. It makes minimal terminal maipulation,
and will keep to very basic vt100/ANSI/«de facto» standard.


Implemented Features
--------------------

* Syntax highlighted through Pygments library
* Linear undo/redo
* Registers
* Macros
* Expantabs
* Windows and vertical splits
* Most basic motions ( W w e E $ gg G b _ 0 h j k l )
* Most basic 



Python Mode
-----------
The repl inside the editor.

    :python
            You are now in a python repl.
            You can access Vy by the «Editor» variable
            risk and profit...
            
            note that you are back in __main__ no matter what this means!
    >>> _

from vy.textfile import TextFile
---------------------------------

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
