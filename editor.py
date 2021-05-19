"""This module contains the implementation of the «editor» class.

When importing Vy as a whole package, an instance of Editor is the only
thing you get. And when executing (python -m), an Editor *instance* shall
be the unique thing in the global dict.
"""
from pathlib import Path

from .cache import Cache
from .screen import Screen
from .interface import Interface
from .console import get_a_key
from .filetypes import ReadOnlyTextFile, TextFile, Folder, HugeFile

class Editor:
    """ This class is the data structure representing the state of the Vym editor.
    The editor class sould not need to be instanciated more than once.
    It is design to be self contained: if you want your code to interract with
    the editor, just pas the «editor» variable to your function.
    """    
    cache = Cache()
    register = dict()
    
    def __init__(self, *buffers):
        self._running_flag = False
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

    def edit(self, location):
        """Changes the current buffer to edit location and set the interface
        accordingly.
        """
        return self.current_window.change_buffer(self.cache.get(location))
    
    @property
    def current_window(self):
        return self.screen.focused

    @property
    def current_buffer(self):
        return self.current_window.buff

    def __call__(self,buff=None):
        """Calling the editor launches the command loop interraction."""
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

