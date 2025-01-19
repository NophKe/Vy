from vy.actions.helpers import atomic_commands as _atomic
from vy.editor import _Editor

@_atomic(':git_commit_all_files :commit_all_files')
def git_commmit_all(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    subprocess.run('EDITOR="python -m vy" git add . && git commit', shell=True)
    editor.start_async_io()
    
@_atomic(':git_commit_known_files :commit_known_files')
def git_commmit_known(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    subprocess.run('EDITOR="python -m vy" git commit -a', shell=True)
    editor.start_async_io()
    
@_atomic(':git_status :status')
def git_status(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    subprocess.run('git status', shell=True)
    subprocess.run('read', shell=True)
    editor.start_async_io()
   

@_atomic(':git_diff :diff')
def git_diff(editor: _Editor, reg=None, part=None, arg=None, count=1):
    import subprocess
    editor.stop_async_io()
    out = subprocess.check_output('git diff', text=True, shell=True)
    editor.edit('/tmp/.vy/last_diff.diff')
    editor.current_buffer.insert(out)
    editor.current_buffer.cursor = 0
    editor.start_async_io()
   
