from vy.actions.helpers import atomic_commands as _atomic
from vy.editor import _Editor

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
def git_status(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    msg = subprocess.getoutput('git status')
#    msg = subprocess.getoutput('git status', shell=True)
    editor.start_async_io()
    msg = msg.expandtabs().splitlines()
    editor.screen.minibar(*msg)
   

@_atomic(':git_diff :diff')
@_only_if_git_repo
def git_diff(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    out = subprocess.check_output('git diff', text=True, shell=True)
    editor.edit('/tmp/.vy/last_diff.diff')
    editor.current_buffer.insert(out)
    editor.current_buffer.cursor = 0
    editor.current_buffer.modifiable = False
    editor.start_async_io()

   
@_atomic(':git_add_and_commit :add_and_commit')
@_only_if_git_repo
def git_add_and_commit(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    ret = subprocess.run('EDITOR="python -m vy" git add --edit || read && git commit', shell=True)
    editor.start_async_io()

@_atomic(':git_add :add')
@_only_if_git_repo
def git_add(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    ret = subprocess.run('EDITOR="python -m vy" git add --edit || read', shell=True)
    if ret.returncode:
        editor.warning(f'error {ret.returncode=}')
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
