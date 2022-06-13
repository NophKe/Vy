from pathlib import Path
from os import access, R_OK, W_OK

from .folder import Folder
from .textfile import TextFile

def Open_path(location):
    if (location is None):
        return TextFile(path=None, init_text='\n')
    elif isinstance(location, str):
        location = Path(location).resolve()
    if not isinstance(location, Path):
        raise TypeError('in function Open_path (Vy/filetypes/__init__.py) argument must be None, str or Path object')
    location = location.resolve()

    try:
        init_text = location.read_text() 
        return TextFile(path=location, init_text=init_text)
    except FileNotFoundError:
        if access(location, W_OK):
            return TextFile(path=location, init_text='\n')
        #raise PermissionError
    except IsADirectoryError:
        return Folder(path=location)
                        
