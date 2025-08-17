from vy.actions.helpers import atomic_commands as _atomic
from vy.actions.with_arg import _CompletableCommand
from vy.editor import _Editor
import subprocess as _subprocess

_git_header = """
    This command is part of command mode «with args» commands.
    Those will not work outside of a valid git repo.
    You may be asked to confirm if you have unsaved work.

    [SYNTAX]      :%s {argument}
    aliases: %s"""

_with_untracked = _CompletableCommand(_git_header, 'git_untracked')
_with_modif = _CompletableCommand(_git_header, 'git_modif_or_untracked')

def _only_if_git_repo(func):
    def wrapped(editor, *args, **kwargs):
        import pathlib
        if not (pathlib.Path.cwd() / '.git').exists():
            raise editor.MustGiveUp('Please open Vy at the top of a git repo or use :cd to move to it')
        return func(editor, *args, **kwargs)
    return wrapped

def _only_if_all_saved(func):
    def wrapped(editor, *args, **kwargs):
        unsaved = len(list(None for buff in editor.cache if buff.unsaved))
        if unsaved:
            editor.confirm(f'You have un-saved work upon {unsaved} file(s).')
        return func(editor, *args, **kwargs)
    return wrapped

@_atomic(':git_commit_all_files :commit_all_files')
@_only_if_git_repo
@_only_if_all_saved
def git_commmit_all(editor: _Editor, reg=None, part=None, arg=None, count=1):
    editor.stop_async_io()
    _subprocess.run('EDITOR="python -m vy" git add . && git commit', shell=True)
    editor.start_async_io()
    
@_atomic(':git_commit_known_files :commit_known_files')
@_only_if_git_repo
@_only_if_all_saved
def git_commmit_known(editor: _Editor, reg=None, part=None, arg=None, count=1):
    editor.stop_async_io()
    _subprocess.run('EDITOR="python -m vy" git commit -a', shell=True)
    editor.start_async_io()
    
@_atomic(':git_status :status')
@_only_if_git_repo
def git_status(editor: _Editor, reg=None, part=None, arg='', count=1):
    editor.stop_async_io()
    msg = _subprocess.getoutput(f'git status {arg}')
    unsaved = len(list(None for buff in editor.cache if buff.unsaved))
    editor.start_async_io()
    msg = msg.expandtabs().splitlines()
    if unsaved:
        msg.append('-----')
        msg.append(f'    {unsaved} unsaved buffer(s) in editor cache.')
    editor.screen.minibar(*msg)

@_with_modif(':git_diff :diff')
@_only_if_git_repo
def git_diff(editor: _Editor, reg=None, part=None, arg='', count=1):
    editor.stop_async_io()
    out = _subprocess.check_output(f'git diff {arg}', text=True, shell=True)
    editor.start_async_io()
    if out:
        filename = '/tmp/.vy/last_diff.diff'
        try:
            del editor.cache[filename]
        except KeyError:
            pass
        editor.edit(filename)
        editor.current_buffer.insert(out)
        editor.current_buffer.cursor = 0
        editor.current_buffer.modifiable = False
    else:
        editor.screen.minibar('everything is up to date')

@_with_modif(':git_add :add')
@_only_if_git_repo
@_only_if_all_saved
def git_add(editor: _Editor, reg=None, part=None, arg='-p', count=1):
    editor.stop_async_io()
    ret = _subprocess.run(f'git add {arg}', shell=True)
    if ret.returncode:
        editor.warning(f'Aborting "git add" error {ret.returncode=}')
    editor.start_async_io()
   
@_atomic(':git_add_and_commit :add_and_commit')
@_only_if_git_repo
def git_add_and_commit(editor: _Editor, reg=None, part=None, arg=None, count=1):
    editor.stop_async_io()
    ret = _subprocess.run('EDITOR="python -m vy" git add --edit', shell=True)
    if ret.returncode:
        editor.warning(f'Aborting "git add" error {ret.returncode=}')
    else:
        ret = _subprocess.run('EDITOR="python -m vy" git commit', shell=True)
        if ret.returncode:
            editor.warning(f'Aborting "git commit" error {ret.returncode=}')
    editor.start_async_io()
    
@_atomic(':git_add_commit_and_push :add_commit_and_push')
@_only_if_git_repo
def git_add_and_commit_and_push(editor: _Editor, reg=None, part=None, arg=None, count=1):
    editor.stop_async_io()
    ret = _subprocess.run('EDITOR="python -m vy" git add --edit', shell=True)
    if ret.returncode:
        editor.warning(f'Aborting "git add" error {ret.returncode=}')
    else:
        ret = _subprocess.run('EDITOR="python -m vy" git commit', shell=True)
        if ret.returncode:
            editor.warning(f'Aborting "git commit" error {ret.returncode=}')
        else:
            ret = _subprocess.run('EDITOR="python -m vy" git push', shell=True)
            if ret.returncode:
                editor.warning(f'Aborting "git push" error {ret.returncode=}')
    editor.start_async_io()

@_atomic(':git_remove_staged :remove_staged')
@_only_if_git_repo
def git_remove_staged(editor: _Editor, reg=None, part=None, arg=None, count=1):
    editor.stop_async_io()
    ret = _subprocess.run('git restore --staged . || read', shell=True)
    if ret.returncode:
        editor.warning(f'error {ret.returncode=}')
    editor.start_async_io()
    
@_atomic(':git_clean_interactive :clean_interactive')
@_only_if_git_repo
def git_clean(editor: _Editor, reg=None, part=None, arg=None, count=1):
    editor.stop_async_io()
    ret = _subprocess.run('git clean --interactive || read', shell=True)
    if ret.returncode:
        editor.warning(f'error {ret.returncode=}')
    editor.start_async_io()
    
@_atomic(':git_push :push')
@_only_if_git_repo
def git_push(editor: _Editor, reg=None, part=None, arg=None, count=1):
    editor.stop_async_io()
    ret = _subprocess.run('git push || read', shell=True)
    if ret.returncode:
        editor.warning(f'error {ret.returncode=}')
    editor.start_async_io()
    
@_with_untracked(':git_clean :clean')
@_only_if_git_repo
def git_clean(editor: _Editor, reg=None, part=None, arg='', count=1):
    show = _subprocess.getoutput(f'git clean --dry-run {arg}')
    if show:
        try:
            editor.confirm(show)
            editor.stop_async_io()
        except editor.MustGiveUp:
            editor.screen.minibar('nothing done')
        else:
            editor.start_async_io()
            ret = _subprocess.run(f'git clean -f {arg}', shell=True)
            if ret.returncode:
                editor.warning(f'error {ret.returncode=}')
    else:
        editor.screen.minibar('nothing to do!')
