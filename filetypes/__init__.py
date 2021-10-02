from pathlib import Path

from .hugefile import HugeFile
from .folder import Folder
from .textfile import TextFile
from .ro_textfile import ReadOnlyTextFile


def Open_path(location):
    if (location is None):
        return TextFile(location)

    if isinstance(location, (Path, str)):
        location = Path(location).resolve()
        if location.is_dir() and location.exists():
            return Folder(location)
        
        if location.exists() and location.is_file():
            if location.lstat().st_size > 1_000_000_000:
                return HugeFile(location)

            #try:
            open(location, 'r').close()
            #except PermissionError as exc:
            #    return ReadOnlyTextFile(None)

            try:
                open(location, 'a').close()
            except PermissionError as exc:
                return ReadOnlyTextFile(location)
            
            return TextFile(location)

        if not location.exists():
            try:
                open(location, 'w').close()
            except PermissionError as exc:
                return ReadOnlyTextFile(location)
            return TextFile(location)

