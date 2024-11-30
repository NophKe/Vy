class _NotWorking(RuntimeError):
    pass
    
def _not_working(*args):
    raise _NotWorking

get_os_clipboard = set_os_clipboard = _not_working

try:
    import copykitten
    get_os_clipboard = copykitten.paste
    set_os_clipboard = copykitten.copy
except ImportError:
    pass

try:
    import pyperclip
    get_os_clipboard = pyperclip.paste
    set_os_clipboard = pyperclip.copy
    _NotWorking = pyperclip.PyperclipException
except ImportError:
    pass

try:
    set_os_clipboard(get_os_clipboard())
except _NotWorking:
    def get_os_clipboard():
        from __main__ import Editor
        return Editor.registr.dico['"']
    
    def set_os_clipboard(new_value):
        from __main__ import Editor
        return Editor.registr.dico.__setitem__('"', new_value)
except BaseException as exc:
    assert False, f'the interraction with os clipboard failed in an unpredicted way {exc=}'
