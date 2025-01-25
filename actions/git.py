from vy.actions.helpers import atomic_commands as _atomic
from vy.actions.with_arg import _CompletableCommand
from vy.editor import _Editor

_git_header = """
    This command is part of command mode «with args» commands.
    Those will not work outside of a valid git repo.

    [SYNTAX]      :%s {argument}
    aliases: %s"""
_with_modif = _CompletableCommand(_git_header, 'git_modif_or_untracked')

def _only_if_git_repo(func):
    def wrapped(editor, *args, **kwargs):
        import pathlib
        if not (pathlib.Path.cwd() / '.git').exists():
            raise editor.MustGiveUp('Please open Vy at the top of a git repo or use :cd to move to it')
        return func(editor, *args, **kwargs)
    return wrapped

@_atomic(':git_commit_all_files :commit_all_files')
@_only_if_git_repo
def git_commmit_all(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    subprocess.run('EDITOR="python -m vy" git add . && git commit', shell=True)
    editor.start_async_io()
    
@_atomic(':git_commit_known_files :commit_known_files')
@_only_if_git_repo
def git_commmit_known(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    subprocess.run('EDITOR="python -m vy" git commit -a', shell=True)
    editor.start_async_io()
    
@_atomic(':git_status :status')
@_only_if_git_repo
def git_status(editor: _Editor, reg=None, part=None, arg='', count=1):
    import subprocess
    editor.stop_async_io()
    msg = subprocess.getoutput(f'git status {arg}')
    editor.start_async_io()
    msg = msg.expandtabs().splitlines()
    editor.screen.minibar(*msg)
   

@_with_modif(':git_diff :diff')
@_only_if_git_repo
def git_diff(editor: _Editor, reg=None, part=None, arg='', count=1):
    import subprocess
    editor.stop_async_io()
    out = subprocess.check_output(f'git diff {arg}', text=True, shell=True)
    editor.start_async_io()
    if out:
        editor.edit('/tmp/.vy/last_diff.diff')
        editor.current_buffer.insert(out)
        editor.current_buffer.cursor = 0
        editor.current_buffer.modifiable = False
    else:
        editor.screen.minibar('everything is up to date')

@_with_modif(':git_add :add')
@_only_if_git_repo
def git_add(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    ret = subprocess.run(f'git add {arg}', shell=True)
    if ret.returncode:
        editor.warning(f'Aborting "git add" error {ret.returncode=}')
    editor.start_async_io()
   
@_atomic(':git_add_and_commit :add_and_commit')
@_only_if_git_repo
def git_add_and_commit(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    ret = subprocess.run('EDITOR="python -m vy" git add --edit', shell=True)
    if ret.returncode:
        editor.warning(f'Aborting "git add" error {ret.returncode=}')
    else:
        ret = subprocess.run('EDITOR="python -m vy" git commit', shell=True)
        if ret.returncode:
            editor.warning(f'Aborting "git commit" error {ret.returncode=}')
    editor.start_async_io()
    
@_atomic(':git_add_commit_and_push :add__commit_and_push')
@_only_if_git_repo
def git_add_and_commit_and_push(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    ret = subprocess.run('EDITOR="python -m vy" git add --edit', shell=True)
    if ret.returncode:
        editor.warning(f'Aborting "git add" error {ret.returncode=}')
    else:
        ret = subprocess.run('EDITOR="python -m vy" git commit', shell=True)
        if ret.returncode:
            editor.warning(f'Aborting "git commit" error {ret.returncode=}')
        else:
            ret = subprocess.run('EDITOR="python -m vy" git push', shell=True)
            if ret.returncode:
                editor.warning(f'Aborting "git push" error {ret.returncode=}')
    editor.start_async_io()

@_atomic(':git_remove_staged :remove_staged')
@_only_if_git_repo
def git_remove_staged(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    ret = subprocess.run('git restore --staged . || read', shell=True)
    if ret.returncode:
        editor.warning(f'error {ret.returncode=}')
    editor.start_async_io()
    
@_atomic(':git_clean :clean')
@_only_if_git_repo
def git_clean(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    ret = subprocess.run('git clean --interactive || read', shell=True)
    if ret.returncode:
        editor.warning(f'error {ret.returncode=}')
    editor.start_async_io()
    
@_atomic(':git_push :push')
@_only_if_git_repo
def git_push(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    ret = subprocess.run('git push || read', shell=True)
    if ret.returncode:
        editor.warning(f'error {ret.returncode=}')
    editor.start_async_io()
