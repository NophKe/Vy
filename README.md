Vy
===

What is Vy?
-----------

Vy is a **light** python implementation of the Vi text editor.

It tries to provide a classic Vi-like interface that aims to be easy to
extend through the python programming interface. As an example you can open 
the editor by typing in the python repl:

    from vy.editor import Editor
    Editor('/etc/fstab')

_note:_ `python -m vy filename` works as well

It does not provide anything like VimScript but tries to expose its internals
in a simple pythonic way. To delete from the cursor to the beginning of the
next word, you can use `dw` in the interface whereas you can from python:

    del Editor.current_buffer['w']

And to move to the end of the file (`G` in the interface):

    Editor.current_buffer.move_cursor('G')

Features
--------

For now quite limited...

* Syntax highlighted through Pygments
* linear undo/redo
* dictionary based modes 
(`CommandMode['save_it_all'] = 'wall'` will create a new valid command mode command )
* incomplete list...


from vy.text_file import TextFile
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
