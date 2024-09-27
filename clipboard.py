def get_os_clipboard():
    from __main__ import Editor
    return Editor.registr.dico['"']

def set_os_clipboard(new_value):
    from __main__ import Editor
    return Editor.registr.dico.__setitem__('"', new_value)

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
except ImportError:
    pass


