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
from vy.keys import C_Q, C_X
from vy.editor import _Editor

@_atomic_commands(':source%')
def execute_python_file(editor: _Editor, reg=None, part=None, arg=None, count=1):
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

@_atomic_commands(f":eval% {C_X} i_{C_X}")
def do_eval_buffer(editor: _Editor, reg=None, part=None, arg=None, count=1):
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
    from traceback import format_exc
    name_space = {}
    try:
        code = compile(editor.current_buffer.string,
                       editor.current_buffer.path,
                       'exec')
    except SyntaxError as exc:
        editor.screen.minibar('syntax error during compilation',
                              *format_exc().splitlines())
    else:
        editor.stop_async_io()
        try:
            exec(code, name_space)
        except BaseException as exc:
            editor.start_async_io()
            editor.warning('syntax error during evaluation:\r\n' +
                                  format_exc().replace('\n', '\r\n'))
        else:
            python.loop(editor, source=name_space)
#        finally:
#            editor.start_async_io()

@_atomic_commands(f'{C_Q} i_{C_Q}')
def do_eval_buffer_until_cursor(editor: _Editor, reg=None, part=None, arg=None, count=1):
    """
    Executes the current file as a Python until it reaches the end of
    the current line.
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
    curbuf = editor.current_buffer
    target_lines = curbuf.splited_lines[:curbuf.current_line_idx+1]
    target = ''.join(target_lines)
    editor.stop_async_io()
    name_space = {}
    exec(target, name_space)
    python.loop(editor, source=name_space)
    
@_atomic_commands('Q')
def ex_mode(editor, reg=None, part=None, arg=None, count=1):
    """
    Fed up of hitting the 'Q' key in vim?  Try the new EX mode !! Use
    the minibar as a python repl.  The Editor can be accessed by the
    'ed' variable.
    ---
    This will evaluate the given expression in the __main__ namespace.
    Any assignment will will be kept.  For more information see 
    ':help vy.interface.ex'.
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


@_atomic_commands(':reload_actions')
def reload_actions(editor :_Editor, *args, **kwargs):
    """
    Reloads the known actions.
    """
    from importlib import reload as _reload
    from vy import actions
    from vy.actions import git    
    from vy.actions import evaluation    
    from vy.actions import macros
    from vy.actions import helpers
    from vy.actions import motions
    from vy.actions import mode_change
    from vy.actions import commands
    from vy.actions import edition
    from vy.actions import with_arg
    from vy.actions import linewise
    _reload(git)    
    _reload(evaluation)    
    _reload(macros)    
    _reload(linewise)
    _reload(with_arg)
    _reload(edition)
    _reload(helpers)
    _reload(motions)
    _reload(mode_change)
    _reload(commands)
    _reload(actions)
    editor._init_actions()

