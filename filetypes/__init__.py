"""
    ****************************************
    ****    The Different File-Types    ****
    ****************************************

Vy has two fundamental buffer types, the folder and the text-file.  Both
are implemented as a python class that inherit from a base class
'BaseFile'.  See ':help vy.filetypes.basefile' for more informations.

The vy.filetype module defines a few mappings of known file extensions
with the appropriate settings.  It is the place for adding custom
settings.

"""
from pathlib import Path
from os import access, W_OK


from .textfile import TextFile
from .folder import Folder

def register_extension(*args):
    def update_ext_dict(cls):
        for arg in args:
            known_extensions[arg] = cls
        return cls
    return update_ext_dict

from vy.global_config import MINI
if not MINI:
    from .pyfile import PyFile, SimplePyFile
    known_extensions = {'.pyx': SimplePyFile,
                    '.pxd': SimplePyFile,
                    '.py' : PyFile,
                    '.txt': TextFile,
                   }
else:
    known_extensions = {}
    @register_extension('.py')    
    class SimplePyFile(TextFile):
        set_wrap = False
        set_autoindent = True
        set_expandtabs = True
        set_number = True
        set_comment_string = ('#', '')

@register_extension('Makefile')
class MakeFile(TextFile):
    set_wrap = True
    set_expandtabs = False
    set_number = True
    set_comment_string = ('#', '')

@register_extension('.html', '.htm', '.xml')
class HtmlFile(TextFile):
    set_wrap = True
    set_autoindent = True
    set_expandtabs = True
    set_number = True
    set_comment_string = ('<!--', '-->')

@register_extension('.c', '.cpp', '.h', '.hpp', '.js', '.css')
class CSyntaxFile(TextFile):
    set_wrap = True
    set_autoindent = True
    set_expandtabs = True
    set_number = True
    set_comment_string = ('/*', '*/')

def Open_path(location):
    """
    The Open_path function is responsible for creating new buffers.
    ---
    If the given path matches a known file extension, buffer locals
    settings will be applied to it.
    ---
    This function allways returns a new object, use it from any python
    repl and save the result in a local variable

    While editing or writing a Vy action Editor.edit() and Editor.cache
    should be prefered as they remember previously visited buffers.
    """
    if location is None:
        return TextFile(path=None, init_text='\n')
        # return a new empty buffer
        
    if isinstance(location, str):
        location = Path(location)
        
    if not isinstance(location, Path):
        raise TypeError('in function Open_path (Vy/filetypes/__init__.py)'
                        ' argument must be None, str or Path object')

    location = location.resolve()
    
    try:
        init_text = location.read_text() 
    except FileNotFoundError:
        if not any(access(ancestor, W_OK) for ancestor in location.resolve().parents):
            raise PermissionError
        init_text = '\n'
    except IsADirectoryError:
        return Folder(path=location)

    init_text = init_text or '\n'
    full_file_name = location.name
    file_name = full_file_name.lower()

    for extension, klass in known_extensions.items():
        if file_name.endswith(extension) or extension in file_name:
            return klass(path=location, init_text=init_text)
    else:
        return TextFile(path=location, init_text=init_text)
