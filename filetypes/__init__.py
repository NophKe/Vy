"""
    ****************************************
    ****    The Different File-Types    ****
    ****************************************

Vy has two fundamental buffer types, the folder and the text-file.  Both
are implemented as a python class that inherit from a base class
'BaseFile'.  See ':help! filetypes.basefile' for more informations.

The vy.filetype module defines a few mappings of known file extensions
with the appropriate settings.  It is the place for adding custom
settings.

"""
from pathlib import Path
from os import access, W_OK

from .folder import Folder
from .textfile import TextFile

known_file_names = {}

known_file_names_tabs = {
    '.css'      : 2,
    '.html'     : 2,
    '.vy.doc'   : 4,
    'Makefile'  : 8,
    '.py'       : 4,
    }

known_file_names_autoindent = {
    '.css'      : True,
    '.html'     : True,
    '.vy.doc'   : True,
    '.py'       : True,
    'Makefile'  : True,
    '.c'        : True,
    }

known_file_names_comment_string = {
    '.vy.doc'   : ('~', ''),
    '.py'       : ('#', ''),
    '.c'        : ('/*', '*/'),
    '.cpp'      : ('/*', '*/'),
    '.css'      : ('/*', '*/'),
    }

known_file_names_wrap = {
    '.vy.doc'   : False,
    '.css'      : False,
    '.html'     : False,
    'Makefile'  : True,
    '.txt'      : True,
    }

known_file_names_expandtabs = {
    '.css'      : True,
    '.html'     : True,
    '.vy.doc'   : False,
    'Makefile'  : False,
    '.py'       : True,
    }

def Open_path(location):
    """
    The Open_path function is responsible for creating new buffers.
    Depending on the given path argument, it will return a 'Folder' or
    a 'TextFile' instance.
    ---
    If the given path matches a known file extension, buffer locals
    settings will be applied to it.
    ---
    This function allways returns a new object, use it from any python
    repl and save the result in a local variable, while editing or
    writing a Vy-script Editor.edit() and Editor.cache should be
    prefered as they remember previously visited buffers.
    """
    if location is None:
        return TextFile(path=None, init_text='\n')
    elif isinstance(location, str):
        location = Path(location).resolve()
    if not isinstance(location, Path):
        raise TypeError('in function Open_path (Vy/filetypes/__init__.py)'
                        ' argument must be None, str or Path object')

    location = location.resolve()
    try:
        init_text = location.read_text() 
    except FileNotFoundError:
        if not any(access(ancestor, W_OK) for ancestor in location.resolve().parents):
            raise PermissionError
        return TextFile(path=location, init_text='\n')
    except IsADirectoryError:
        return Folder(path=location)

    file_name = location.name.lower()
    file_other_name = location.name

    if file_name in known_file_names:
        return known_file_names[file_name](path=location, init_text=init_text)
    if '\t' in init_text:
        expand_tabs = False
    else:
        for name in known_file_names_expandtabs:
            if file_name.endswith(name) or file_other_name.endswith(name):
                expand_tabs = known_file_names_expandtabs[name]
                break
        else:
            expand_tabs = False

    for name in known_file_names_tabs:
        if file_name.endswith(name) or file_other_name.endswith(name):
            tab_size = known_file_names_tabs[name]
            break
    else:
        tab_size = 4

    for name in known_file_names_wrap:
        if file_name.endswith(name) or file_other_name.endswith(name):
            wrap = known_file_names_wrap[name]
            break
    else:
        wrap = False

    for name in known_file_names_comment_string:
        if file_name.endswith(name) or file_other_name.endswith(name):
            comment_string = known_file_names_comment_string[name]
            break
    else:
        comment_string = ('', '')
    
    for name in known_file_names_autoindent:
        if file_name.endswith(name) or file_other_name.endswith(name):
            autoindent = known_file_names_autoindent[name]
            break
    else:
        autoindent = False

    return TextFile(path=location, 
                    init_text=init_text, 
                    set_autoindent=autoindent,
                    set_tabsize=tab_size,
                    set_expandtabs=expand_tabs,
                    set_comment_string=comment_string,
                    set_wrap=wrap,
                    )
