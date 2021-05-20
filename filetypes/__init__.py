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
        if location.is_dir():
            return Folder(location)
        
        if location.exists() and location.is_file():
            if location.lstat().st_size > 1_000_000_000:
                return HugeFile(location)

            try:
                open(location, 'r')
            except PermissionError as exc:
                return self.current_buffer

            try:
                open(location, 'a')
            except PermissionError as exc:
                return ReadOnlyTextFile(location)
            
            return TextFile(location)

        if not location.exists():
            try:
                open(location, 'w')
            except PermissionError as exc:
                # TODO # replace that input func by call to ed.warning
                input('you do not seem to have the rights to write in here.')
                return self.current_buffer
            return TextFile(location)

