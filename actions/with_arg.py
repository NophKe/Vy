"""
Those are the command-mode commands that can take an argument Depending on how
the argument will be named, you will get differnet autocompletion.
"""
from vy.actions.helpers import _command
from vy.editor import _Editor

class _CompletableCommand(_command):
    category = "with_args"
    def __init__(self, header, completer):
        self.c_header = header
        self.completer = completer
    def update_func(self, alias, func):
        func = super().update_func(alias, func)
        if self.completer:
            func.completer = self.completer
            if func.__doc__:
                func.__doc__ += """
    ---
    NOTE: Use <TAB> to list possible completions."""
        return func
        
_c_with_args_header = """
    This command is part of command mode «with args» commands.

    [SYNTAX]      :%s {argument}
    aliases: %s"""
_with_args = _CompletableCommand(_c_with_args_header, '')

_c_with_filename_header = """
    This command is part of command mode «with filename» commands.

    [SYNTAX]      :%s {filename}
    aliases: %s"""
_with_filename = _CompletableCommand(_c_with_filename_header, 'filename')

_c_with_buffer_header = """
    This command is part of command mode «with cached buffer» commands.

    [SYNTAX]      :%s {cached_buffer}
    aliases: %s"""
_with_buffer = _CompletableCommand(_c_with_buffer_header, 'buffer')

@_with_filename(':w :write')
def do_try_to_save(editor, reg=None, part=None, arg=None, count=1):
    """
    Saves the current buffer. If {filename} is given, saves as this
    new name modifying the current buffer to point to this location.
    """
    if not arg:
        if not editor.current_buffer.unsaved:
            return
        elif editor.current_buffer.path:
            try:
                return editor.current_buffer.save()
            except (IsADirectoryError, FileExistsError, PermissionError) as exc:
                editor.warning(f'{exc.__doc__} quit without saving (:q!) or try to force saving (:w!)')
        else:
            editor.warning('give your file a path (:w some_name) or forget it (:q!).')
    elif arg:
        try:
            return editor.current_buffer.save_as(arg)
        except (IsADirectoryError, FileExistsError, PermissionError) as exc:
            editor.warning(f'{exc.__doc__} quit without saving (:q!) or try to force saving (:w!)')

@_with_args(':reg :registers :di :display :show_register_content')
def show_registers(editor, reg=None, part=None, arg=None, count=1):
    """
    Shows the content of registers.
    If an argument is given, only shows the content of this register.
    """
    if arg:
        if arg in editor.registr:
            editor.warning(arg + ': ' + str(editor.registr[arg]))
        else:
            editor.warning(f'{arg} is not a valid register')
    else:
        editor.warning(str(editor.registr))
    return 'normal'

@_with_buffer(":bd :bdel :bdelete :forget_this_buffer_dont_save")
def do_remove_cached_buffer(editor, reg=None, part=None, arg=None, count=1):
    """
    Deletes a buffer from the cache.
    """
    if arg is None:
        buffer = editor.current_buffer
    else:
        buffer = editor.cache[arg]
    del editor.cache[buffer]
    
    for window in editor.screen:
        if window.buff is buffer:
            if window is editor.screen:
                window.change_buffer(editor.cache['.'])
            elif window is window.parent.left_panel:
                window.parent.merge_from_right_panel()
            elif window is window.parent.right_panel:
                window.parent.merge_from_left_panel()

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
    ---
    NOTE: This command does not follow the vim-syntax.  The main
    difference being the use of spaces to delimit {rhs} and {lhs}.
    ---
    NOTE: In Vy, a space is *allways* needed after the command and
    before the first argument.
    """
    if ' ' in arg:
        rhs, lhs = arg.split(' ', maxsplit=1)
        editor.current_buffer.current_line = editor.current_buffer.current_line.replace(rhs, lhs)
    else:
        editor.warning(substitute.__doc__)

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
    from subprocess import run
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

_c_with_option_header = """
    This command is part of command mode «with args» commands.

    [SYNTAX]      :%s                      >>> show help
    [SYNTAX]      :set {argument}          >>> set to True
    [SYNTAX]      :set no{argument}        >>> set to False
    [SYNTAX]      :set {argument}!         >>> toggle True/False
    [SYNTAX]      :set {argument} {number} >>> set to integer value
    aliases: %s"""
_with_option = _CompletableCommand(_c_with_option_header, 'option')

@_with_option(":set :se")
def do_set(editor, reg=None, part=None, arg=None, count=1):
    """
    Sets an option. Valid options are all buffer attributes starting
    with 'set_*'.
    """
    if not arg:
        raise editor.MustGiveUp(do_set.__doc__)

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

@_with_args(':draw_box')
def draw_a_box_around_text(editor, reg=None, part=None, arg=' ', count=1):
    txt = '    ****    ' + arg.strip().title() + '    ****'
    line = '    ' + '*' * (len(txt)-4) + '\n'
    to_insert = line + txt + '\n' + line
    with editor.current_buffer as cur_buf:
        cur_buf.cursor_lin_col = cur_buf.current_line_idx, 0
        cur_buf.insert(to_insert)

@_with_args(':grep')
def grep_in_directory(editor: _Editor, arg=None, *args, **kwargs):
    """
    Scan for occurences of a pattern in files within the current directory.
    """
    from subprocess import run, TimeoutExpired
    if not arg:
        editor.warning(grep_in_directory.__doc__)
        return 'normal'
    
    command = f"grep -T -n -r {arg}"
    try:
        completed = run(command, capture_output=True, shell=True, text=True, timeout=4)
    except TimeoutExpired:
        raise editor.MustGiveUp('this command got cancelled for beeing too long')
        
    if completed.returncode:
       raise editor.MustGiveUp(f"error while evaluating '{command}'")
    
    editor.warning(completed.stdout)
        
