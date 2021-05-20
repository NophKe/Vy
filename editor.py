"""This module contains the implementation of the «editor» class.

When importing Vy as a whole package, an instance of Editor is the only
thing you get. And when executing (python -m), an Editor *instance* shall
be the unique thing in the global dict.
"""
from pathlib import Path

from .screen import Screen
from .interface import Interface
from .console import get_a_key
from .filetypes import Open_path

# helper function

class Cache():
    """Simple wrapper around a dict that lets you index a buffer by its
    internal id, or any relative or absolute version of its path.
    It only has two public methods: get() and pop().
    - get() creates a new buffer if needed or returns the cached version.
    - pop() lets you uncache a buffer.
    """
    __slots__ = ()
    _dic = dict()
    _counter = 1

    @staticmethod
    def _make_key(key):
        if isinstance(key, int):
            return key
        elif isinstance(key, str):
           return str(Path(key).resolve()) 
        elif isinstance(key, Path):
            return str(key.resolve())
        else:
            raise ValueError

    def pop(self, key):
        """ Use this function to delete a buffer from cache. """
        return self._dic.pop(self._make_key(key))

    def __repr__(self):
        rv = str()
        for buff in self._dic.values():
            rv += f'cache_id: {buff.cache_id} : {repr(buff)}\n'
        return rv

    def __iter__(self):
        for value in self._dic.values():
            yield value
    
    def __contains__(self, key):
        if key in self._dic:
            return True
        elif self._make_key(key) in self._dic:
            return True
        else:
            return False

    def get(self, item):
            """This is the main api of this class.

            It takes an only argument that can be a string, a path object,
            an int, or None. 

            If the argument is a string or a path object, it will be resolved 
            to an absolute path, and if this path has allready been cached,
            the correponding buffer will be returned. If not, a new buffer
            will be created from reading the path content or from scratch.
            Pass it an integer to reach buffers unrelated to file system.
            Pass it None to create a new unnamed buffer.
            """
            if (key := self._make_key(item)) in self._dic:
                return self._dic[key]
            else:
                if name is None:
                    buff = Open_path(**kwargs)
                    self._dic[self._counter] = buff
                    buff.cache_id = self._counter
                    self._counter +=1
                    return buff
                else:
                    self._dic[name] = Open_path(name, **kwargs)
                    rv = self._dic[name]
                    rv.cache_id = name
                    return rv

class Register:
    __slots__ = ()
    dico = dict()

    def __repr__(self):
        rv = str()
        for k,v in self.dico.items():
            rv += f'{k}: {v}\n'
        return rv

    def __getitem__(self, key):
        try:
            return self.dico[key]
        except KeyError:
            return ''

    def __setitem__(self, key, value):
        assert isinstance(value, str)
        if key == '"':
            self.dico['"'] = value
        elif key.isupper():
            self.dico[key.lower()] += value
        else:
            self.dico[key] = value
        
class Editor:
    """ This class is the data structure representing the state of the Vym editor.
    The editor class sould not need to be instanciated more than once.
    It is design to be self contained: if you want your code to interract with
    the editor, just pas the «editor» variable to your function.
    """    
    cache = Cache()
    register = Register()
    
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

        self.screen.alternative_screen()
        self.screen.clear_screen()
        self.screen.show(True)
        mode = 'normal'
        try:
            while True:
                mode = self.interface(mode)
        finally:
            self.screen.original_screen()

