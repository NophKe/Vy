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
import pkgutil
import importlib
from vy.filetypes.textfile import TextFile

known_extensions = {}

def _register_extension(*args):
    def update_ext_dict(klass):
        for arg in args:
            known_extensions[arg] = klass
        return klass
    return update_ext_dict

# Automatically import all submodules when package is imported
for _, module_name, _ in pkgutil.walk_packages(__path__, prefix=__name__ + "."):
    importlib.import_module(module_name)

@_register_extension('Makefile')
class MakeFile(TextFile):
    set_wrap = True
    set_expandtabs = False
    set_number = True
    set_comment_string = ('#', '')

@_register_extension('.cpp', '.h', '.hpp')
class CSyntaxFile(TextFile):
    set_wrap = True
    set_autoindent = True
    set_expandtabs = True
    set_number = True
    set_comment_string = ('/*', '*/')
    _lsp_server = ['ccls']
    _lsp_lang_id = 'c'

@_register_extension('.f90')
class FortranFile(TextFile):
    _lsp_server = 'wtf'
    
@_register_extension('.kt')
class KotlinFile(TextFile):
    _lsp_server = 'kotlin-language-server'
    _lsp_lang_id = ''

def Open_path(location):
    """
    The Open_path function is responsible for creating new buffers.
    ---
    If the given path matches a known file extension, buffer locals
    settings will be applied to it.
    ---
    This function allways returns a new object, use it from any python
    repl and save the result in a local variable.

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
