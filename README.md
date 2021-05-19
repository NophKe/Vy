Vy
===

What is Vy?
-----------

Vy is a **light** python implementation of the Vi text editor. It has 
no external dependency outside standard lib. But it can use the Pygments
library (if present) for syntax highlighting.  It aims to stay below 3000
lines (including doc) and run on any modern python machine.

It tries to provide a classic Vi-like interface that aims to be easy to
extend through the python programming interface. As an example you can open 
the editor by typing in the python repl:

    from vy.editor import Editor
    Editor('/etc/fstab')

_note:_ otherwise use `python -m vy filename` ;-) 


It does not provide anything like VimScript but tries to expose its internals
in a simple pythonic way. To delete from the cursor to the beginning of the
next word, you can use `dw` in the interface whereas you can from python:

    del Editor.current_buffer['w']

And to move to the end of the file (`G` in the interface):

    Editor.current_buffer.move_cursor('G')

Features
--------

- w/b/e/$/_ moves (can take counts like 10w)
- h/j/k/l of course! + cursor keys
- A/I for insert mode on end/beginning of line.
- a/i for insert mode after/before cursor.
- O/o for insert mode on a new line.
- zt/zz/zb for screen navigation
- page up/down
- :line_number go reach this line
- :w/:wa/:wall/:wq/:wqa/:wqall etc...
- :vsplit


For now quite limited...

* Syntax highlighted through Pygments
* linear undo/redo
* dictionary based modes 
(`CommandMode['save_it_all'] = 'wall'` will create a new valid command mode command )
* incomplete list...

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
