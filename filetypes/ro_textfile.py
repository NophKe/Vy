from .motions import Motions
from .syntax import view
from ..behaviour import ReadOnlyText 

class ReadOnlyTextFile(view, ReadOnlyText):
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

