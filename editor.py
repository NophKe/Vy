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

class Cache():
    """Simple wrapper around a dict that lets you index a buffer by its
    internal id, or any relative or absolute version of its path. use:

    >>> x = Cache()
    >>> x['/home/Nono/test.txt']
       TextFile('/home/Nono/test.txt')
    >>> x['/home/Nono/test.txt'] is x['./test.txt']
       True
    >>> del x['test.txt']
    >>> '../nono/test.txt' in x
       False

    Note: You may create as many of them as you want. The wrapped dict 
        being a class attribute. All instances will have access to it.
    """
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

    def __delitem__(self, key):
        """ Use this function to delete a buffer from cache. """
        return self._dic.pop(self._make_key(key))

    def __repr__(self):
        return repr(self._dic)

    def __str__(self):
        rv = 'cache id    :    cached file\n'
        for buff in self._dic.values():
            rv += f'{buff.cache_id}    :    {repr(buff)}\n'
        return rv

    def __iter__(self):
        for value in self._dic.values():
            yield value
    
    def __contains__(self, key):
        if self._make_key(key) in self._dic:
            return True
        return False

    def __getitem__(self, key):
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
        if key is None:
            buff = Open_path(key)
            self._dic[self._counter] = buff
            buff.cache_id = self._counter
            self._counter +=1
            return buff

        if (key := self._make_key(key)) in self._dic:
            return self._dic[key]
            
        self._dic[key] = Open_path(key)
        rv = self._dic[key]
        rv.cache_id = key
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
        if isinstance(key, int):
            key = str(key)
        assert isinstance (key, str)
        try:
            return self.dico[key]
        except KeyError:
            return ''

    def __setitem__(self, key, value):
        if isinstance(key, int):
            key = str(key)
        assert isinstance(key, str)

        if key == '_':
            return
        elif key == '"':
            for k in range(9,0,-1):
                self[k] = self[k-1]
            self[0] = self['"']
            self.dico['"'] = value
        elif key.isupper():
            self.dico[key.lower()] += value
        elif key.islower() or key.isnumeric():
            self.dico[key] = value
        elif key == '=':
            self.dico[key] = eval(key)
        
class Editor:
    """ This class is the data structure representing the state of the Vym editor.
    The editor class sould not need to be instanciated more than once.
    It is design to be self contained: if you want your code to interract with
    the editor, just pass the «editor» variable to your function.
    """    
    cache = Cache()
    register = Register()
    
    def __init__(self, *buffers):
        self._macro_keys = ''
        self._running = False
        if buffers:
            for buff in buffers:
                self.cache[buff]
        self.screen = Screen(self.cache[None if not buffers else buffers[0]])
        self.interface = Interface(self)
    
    def read_stdin(self):
        if self._macro_keys:
            rv = self._macro_keys[0]
            self._macro_keys = self._macro_keys[1:]
            return rv
        return get_a_key()
    
    def push_macro(self, string):
        assert isinstance(string, str)
        self._macro_keys = f'{string}{self._macro_keys}'
        

    def warning(self, msg):
        """Displays a warning message to the user. This should be the main way to cast
        information to the screen during the execution of a command as it allows the 
        user to enter the debugger if needed.
        In parts of the runtime where this method can't be reached, just use input()
        """
        assert isinstance(msg, str)
        self.screen.minibar(f"{msg}\r\n\tpress any key to continue (or ^c to debug...)")
        if (key := get_a_key()) == '\x03':
            print('\nyou are now in debugger. use \'cont\' to resume\n')
            breakpoint()

    def edit(self, location):
        """Changes the current buffer to edit location and set the interface
        accordingly.
        """
        return self.current_window.change_buffer(self.cache[location])
    
    @property
    def current_window(self):
        return self.screen.focused

    @property
    def current_buffer(self):
        return self.current_window.buff

    def __call__(self,buff=None):
        """Calling the editor launches the command loop interraction."""
        if self._running is True:
            print("\tYou cannot interract with the editor stacking call to")
            print("\t«Editor» instance.")
            print("\tInstead use Editor.interface('insert')")
            input("press [enter] to continue")
            return
        self._running = True
        if (buff is not None) or self.current_buffer is None:
            self.edit(buff)
            self.screen = Screen(self.current_buffer)

        self.screen.alternative_screen()
        self.screen.clear_screen()
#        self.screen.show(True)
        mode = 'normal'
        try:
            while True:
                mode = self.interface(mode)
#       except:
#           ans = ''
#           while ans.strip().lower() not in 'rep':
#               print('An exception occured what do you want to do?')
#               print()
#               print('[R]aise the exception')
#               print('[E]nter debugger')
#               print('[P]ass silently')            
#               ans = input()
#           if ans in 'rR':
#               raise
#           elif ans in 'eE':
#               breakpoint()
#           elif ans in 'pP':
#               pass
        finally:
            self.screen.original_screen()

