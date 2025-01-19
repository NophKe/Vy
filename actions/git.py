###
# Start of shamefull code duplication
###

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

###
# End of shamefull code duplication
###
_c_with_git_header = """
    This command is part of command mode «with filename» commands.

    [SYNTAX]      :%s {git command}
    aliases: %s"""
_with_git = _CompletableCommand(_c_with_git_header, 'git')

@_with_git(':git_commit_all_files :commit_all_files')
def git_commmit_all(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    subprocess.run('EDITOR="python -m vy" git add . && git commit', shell=True)
    editor.start_async_io()
    
@_with_git(':git_status :status')
def git_status(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    subprocess.run('git status', shell=True)
    subprocess.run('read', shell=True)
    editor.start_async_io()
   

@_with_git(':git_diff :diff')
def git_diff(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    out = subprocess.check_output('git diff', text=True, shell=True)
    editor.edit('/tmp/.vy/last_diff.diff')
    editor.current_buffer.insert(out)
    editor.current_buffer.cursor = 0
    editor.start_async_io()
   
