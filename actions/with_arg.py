from vy.actions.helpers import with_args_commands as _with_args
from vy.actions.helpers import command as _command

class _CompletableCommand(_command):
    def __init__(self, header, completer):
        super().__init__(header, None, None, None, "with_args")
        self.completer = completer
    def update_func(self, alias, func):
        func = super().update_func(alias, func)
        func.completer = self.completer
        return func
        
_c_with_args_header = """
    This command is part of command mode «with args» commands.

    [SYNTAX]      :%s {argument}
    aliases: %s
    -------------------------------------------------------------------- """
_with_args = _CompletableCommand(_c_with_args_header, '')

_c_with_filename_header = """
    This command is part of command mode «with filename» commands.

    [SYNTAX]      :%s {filename}
    aliases: %s
    -------------------------------------------------------------------- """
_with_filename = _CompletableCommand(_c_with_filename_header, 'filename')


_c_with_buffer_header = """
    This command is part of command mode «with cached buffer» commands.

    [SYNTAX]      :%s {cached_buffer}
    aliases: %s
    -------------------------------------------------------------------- """
_with_buffer = _CompletableCommand(_c_with_buffer_header, 'buffer')


@_with_buffer(":b :bu :buf :buffer")
def do_edit_cached_buffer(editor, reg=None, part=None, arg=None, count=1):
    """
    Reopens for editing a file that has allready been visited. Similar to
    :e except for auto-completion in prompt.
    """
    if arg:
        editor.edit(arg)


@_with_filename(":e :edit :ex")
def do_edit(editor, reg=None, part=None, arg=None, count=1):
    """
    Start editing a file in the current window. If the file has allready
    being visited, the file is not read again and the cached version in served
    """
    if arg:
        editor.edit(arg)

@_with_args(':%s')
def replace_all(editor, reg=None, part=None, arg=None, count=1):
    """
    WIP !
    """
    if not arg or not ' ' in arg:
        editor.warning('bad syntax')
        return
    with editor.current_buffer as curbuf:
        old, new = arg.split(' ', maxsplit=1)
        for idx, line in enumerate(curbuf.splited_lines):
            curbuf._splited_lines[idx] = line.replace(old, new)
        curbuf._lines_offsets.clear()
        curbuf._string = ''.join(curbuf._splited_lines)
        curbuf._lengh = len(curbuf._string)

@_with_args(':s :su :substitute')
def substitute(editor, arg=None, **kwargs):
    """
    [SYNTAX]      :s {rhs} {lhs}          
    Replace {rhs} by {lhs} on current line.
    """
    if not arg or ' ' not in arg:
        editor.warning(substitute.__doc__)
        return
    rhs, lhs = arg.split(' ', maxsplit=1)
    editor.current_buffer.current_line = editor.current_buffer.current_line.replace(rhs, lhs)

@_with_args(':debug')
def debug_tool(editor, reg=None, part=None, arg='reload', count=1):
    from vy import debug_tools
    func = getattr(debug_tools, arg, None)
    if func is None:
        from pprint import pformat
        valid = [item for item in dir(debug_tools) if not item.startswith('_')]
        editor.screen.minibar('debug func not found', *pformat(valid).splitlines())
    else:
        func(editor)


@_with_args(':map :nmap :nnoremap')
def do_nmap(editor, reg=None, part=None, arg=None, count=1):
    """
    WIP    WARNING RECURSIVE MAPPING !!!!
    """
    if not arg or not ' ' in arg:
        editor.minibar('[SYNTAX]    :nmap [key] [mapping]')
        return
    key, value = arg.split(' ', maxsplit=1)
    func = lambda ed, *args, **kwargs: ed.push_macro(value)
    # feels like a hack! I don't like it.
    func.motion = False
    func.atomic = True
    editor.actions.normal[key] = func



@_with_filename(":read :re :r")
def read_file(editor, reg=None, part=None, arg=None, count=1):
    """
    Reads the content of file specified as argument and inserts it at the
    current cursor location.
    TODO: No check is done by this function. May raise exception!
    """
    from pathlib import Path
    if not arg:
        editor.screen.minibar('Commmand needs arg!')
        return
    editor.current_buffer.insert(Path(arg).read_text())


@_with_args(":!")
def do_system(editor, reg=None, part=None, arg=None, count=1):
    """
    Execute a system command.
    """
    from subprocess import run, CalledProcessError
    if not arg:
        editor.warning('Commmand needs arg!')
    else:
        completed = run(arg, capture_output=True, shell=True, text=True)
        retval = completed.returncode
        output = completed.stdout + completed.stderr
        editor.warning( f'{output}\nCommand Finished with status: {retval or "OK"}')
    
@_with_filename(":chdir :chd :cd")
def do_chdir(editor, reg=None, part=None, arg=None, count=1):
    """
    Change current directory
    """
    if not arg:
        editor.screen.minibar('Commmand needs arg!')
        return
    import os
    try:
        os.chdir(arg)
    except FileNotFoundError:
        editor.warning(f'File not found: {arg}')
    except NotADirectoryError:
        editor.warning(f'Not a directory: {arg}')

@_with_args(":set :se")
def do_set(editor, reg=None, part=None, arg=None, count=1):
    """
    [SYNTAX]      :set {argument}          >>> set to True
    [SYNTAX]      :set no{argument}        >>> set to False
    [SYNTAX]      :set {argument}!         >>> toggle True/False
    [SYNTAX]      :set {argument} {number} >>> set to integer value
    """

    if not arg:
        editor.warning(do_set.__doc__)
        return

    toggle = object()

    arg = arg.strip().lower()
    if ' ' in arg:
        arg, value = arg.split(' ', maxsplit=1)
        value = int(value)
    elif arg.startswith('no'):
        arg = arg[2:]
        value = False
    elif arg.endswith('!'):
        arg = arg[:-1]
        value = toggle
    else:
        value = True

    try:
        option = getattr(editor.current_buffer, 'set_' + arg)
    except AttributeError:
        editor.screen.minibar(f"Invalid option {arg}")
        return

    if isinstance(option, type(value)):
        setattr(editor.current_buffer, f'set_{arg}', value)
    if value is toggle:
        setattr(editor.current_buffer, f'set_{arg}', not option)
