from pathlib import Path
from os import access, R_OK, W_OK

from .hugefile import HugeFile
from .folder import Folder
from .textfile import TextFile
from .ro_textfile import ReadOnlyTextFile


def Open_path(location):
    if (location is None):
        return TextFile(path=None,init_text='\n')
    elif isinstance(location, str):
        location = Path(location).resolve()
    if not isinstance(location, Path):
        raise TypeError('in function Open_path (Vy/filetypes/__init__.py) argument must be None, str or Path object')
    location = location.resolve()

    try:
        init_text = location.read_text() 
    except FileNotFoundError:
        try:
            location.touch()
            location.unlink()
            return TextFile(path=location, init_text='\n')
        except PermissionError:
            raise # to be explicit

    except IsADirectoryError:
        try:
            return Folder(location)
        except PermissionError:
            raise
                        
    if access(location, W_OK):
        return TextFile(path=location, init_text=init_text)
    else:
        return ReadOnlyTextFile(path=location, init_text=init_text)



