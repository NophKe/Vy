from pathlib import Path
from os import access, W_OK

from .folder import Folder
from .textfile import TextFile


known_file_names_tabs = {
    'Makefile'  : 8,
    '.py'       : 4,
    }

known_file_names_autoindent = {
    '.py'       : True,
    'Makefile'  : True,
    '.c'        : True,
    }

known_file_names_comment_string = {
    '.py'       : ('#', ''),
    '.c'        : ('/*', '*/'),
    }

known_file_names_wrap = {
    'Makefile'  : True,
    '.txt'      : True,
    }

known_file_names_expandtabs = {
    'Makefile'  : False,
    '.py'       : True,
    }

def Open_path(location):
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
        if not access(location.parent, W_OK):
            raise PermissionError
        return TextFile(path=location, init_text='\n')
    except IsADirectoryError:
        return Folder(path=location)


    file_name = location.name
    file_other_name = file_name.lower()

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
