"""
    *********************************
    ****    Evaluating Python    ****
    *********************************

Vy has several facilities to execute python code.  As there is no
equivalent for Vimscript, access to python runtime is not prevented.

The commands listed here provide ways to execute native python code.

ATTENTION:
----------
  You are supposed to know what you are doing.  You are supposed to
  understand the python import system and immutability of modules.

Some of the commands listed here involve the 'Ex' and the 'python' mode.
See ':help! interface.ex' and ':help! interface.python' for more.
"""
from vy.actions.helpers import sa_commands as _sa_commands
from vy.actions.helpers import atomic_commands as _atomic_commands

@_atomic_commands(':source%')
def execute_python_file(editor, reg=None, part=None, arg=None, count=1):
    """
    Executes the current file as a Vy script.
    --- 
    The content of the current buffer will be passed to exec() with the
    global (__main__) namespace.  You can use the «Editor» variable to
    interract with the editor.
    ---
    This command should be used to load user-configuration or to debug
    Vy's internals as it can possibly crash the editor.  If you only
    want to execute some random code you happen to be editing use
    ':eval'.

    """
    from __main__ import __dict__ as main_dict
    exec(editor.current_buffer.string, main_dict)

@_atomic_commands(":eval%")
def do_eval_buffer(editor, reg=None, part=None, arg=None, count=1):
    """
    Executes the current file as a Python script.
    ---
    The content of the current buffer will be passed to exec() with a
    new empty namespace.  Beware that allready imported modules will not
    be reloaded.  (This creates a new namespace, but it is not a new
    instance of the python interpreter.)
    To interract with the editor, use 'from __main__ import Editor'.
    ---
    If the code does not raise an exception.  You will be brought to
    «python» mode inside the newly populated namespace.
    """
    from vy.interface import python
    name_space = {}
    editor.stop_async_io()
    exec(editor.current_buffer.string, name_space)
    return python.loop(editor, source=name_space)

@_atomic_commands('Q')
def ex_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Fed up of hitting the 'Q' key in vim?  Try the new EX mode !! Use
    the minibar as a python repl.  The Editor can be accessed by the
    'Editor' variable.
    ---
    This will evaluate the given expression in the __main__ namespace.
    Any assignment will will be kept.  For more information see 
    ':help! interface.ex'.
    """
    return 'ex'

@_atomic_commands(':mode')
def change_mode(editor, arg=None, **kwargs):
    """
    Change the current mode to the one specified by arg.
    """
    try:
        return arg
    except ModuleNotFoundError:
        editor.screen.minibar(' ( mode: «{arg}» not found )')

doc_outro = """
The commands shown here all execute the code inside the current
interpreter instance.  This presents the advantage of allowing access to
Vy's runtime, (like inserting the string representation of a computed
result directly into the current buffer), but this also has drawbacks
when it comes to security.

If you don't trust your code, if you want to garanty all modules are
freshly imported, and you don't need to access the Vy runtime.  You may
as well use the ':!' command.  See ':help :!' for more.

Also, you are un-aware of ':python' and ':python!' commands read next
section.
"""
