#from .motions import Motions
#from .syntax import WindowGenerator
#from ..behaviour import ReadOnlyText 
from .textfile import TextFile

class ReadOnlyTextFile:
    def __repr__(self):
        return f"read-only buffer: {self.path.name if self.path else 'undound to file system'}"

    def write(self, *args, **kwargs):
        pass

    def save_as(self, new_path, **kwargs):
        from .__init__ import Open_path
        pass

    @property
    def unsaved(self):
        return False

