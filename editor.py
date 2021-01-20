from pathlib import Path

from .cache import Cache
from .screen import Screen
from .interface import Interface
from .console import get_a_key
from .filetypes import ReadOnlyTextFile, TextFile, Folder, HugeFile

class Editor:
    cache = Cache()
    register = dict()
    
    def __init__(self, *buffers):
        if buffers:
            for buff in buffers:
                self.cache.get(buff)
        self.screen = Screen(self.cache.get(None if not buffers else buffers[0]))
        self.interface = Interface(self)

    def warning(self, msg):
        assert isinstance(msg, str)
        self.screen.minibar(f"{msg}\r\n\tpress any key to continue (or ^c to debug...)")
        if (key := get_a_key()) == '\x03':
            print('\nyou are now in debugger. use \'cont\' to resume\n')
            breakpoint()

    def open_file(self, location):
        if (location is None) or (location in self.cache):
            return self.cache.get(location)

        if isinstance(location, (Path, str)):
            location = Path(location).resolve()
            if location.is_dir():
                #self.warning('directories!: Not Implemented')
                return Folder(location)
            
            if location.is_file() and location.exists():
                if location.lstat().st_size > 1_000_000_000:
                    return HugeFile(location)

                try: open(location, 'r')
                except PermissionError as exc:
                    self.warning(str(exc.__cause__))
                    return self.current_buffer

                try: open(location, 'a')
                except PermissionError as exc:
                    #self.warning('read-only file: Not Implemented')
                    return ReadOnlyTextFile(location)

            if not location.exists():
                try: open(location, 'w')
                except PermissionError as exc:
                    self.warning('you do not seem to have the rights to write in here.')
                    return self.current_buffer
            # fallback with cache
            return self.cache.get(location)
        else:
            raise ValueError
                
    def edit(self, buff):
        return self.current_window.change_buffer(self.open_file(buff))
    
    @property
    def current_mode(self):
        return {}

    @property
    def current_window(self):
        return self.screen.focused

    @property
    def current_buffer(self):
        return self.current_window.buff

    def __call__(self,buff=None):
        if (buff is not None) or self.current_buffer is None:
            self.edit(buff)
            self.screen = Screen(self.current_buffer)
        #return self.cmdloop()

        self.screen.alternative_screen()
        self.screen.clear_screen()
        self.screen.show(True)
        mode = 'normal'
        try:
            while True:
                mode = self.interface(mode)
        finally:
            self.screen.original_screen()

