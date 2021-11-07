"""This module contains the implementation of the «editor» class.

When importing Vy as a whole package, an instance of Editor is the only
thing you get. And when executing (python -m), an Editor *instance* shall
be the unique thing in the global dict.
"""
from pathlib import Path
from traceback import print_tb
from bdb import BdbQuit
from functools import partial

from vy.screen import Screen
from vy.interface import Interface
from vy.console import get_a_key
from vy.filetypes import Open_path

class _Cache():
    """Simple wrapper around a dict that lets you index a buffer by its
    internal id, or any relative or absolute version of its path. use:

    >> x = Cache()
    >> x['/home/Nono/test.txt']
      TextFile('/home/Nono/test.txt')
    >> x['/home/Nono/test.txt'] is x['./test.txt']
      True
    >> del x['test.txt']
    >> '../nono/test.txt' in x
    False
    """
    def __init__(self):
        self._dic: dict = dict()
        self._counter: int = 1

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

        key = self._make_key(key)
        if key in self._dic:
            return self._dic[key]
            
        self._dic[key] = Open_path(key)
        rv = self._dic[key]
        rv.cache_id = key
        return rv

#    @staticmethod
    def _make_key(self, key):
        if isinstance(key, int):
            return key
        elif isinstance(key, str):
           return str(Path(key).resolve()) 
        elif isinstance(key, Path):
            return str(key.resolve() if not key.is_absolute() else key)
        raise ValueError(f"key is type:{key.__class__}, int, str, or Path expected")

    def __delitem__(self, key):
        """ Use this function to delete a buffer from cache. """
        self._dic.pop(self._make_key(key))

    def __repr__(self):
        return repr(self._dic)

    def __str__(self):
        rv = ''
        for buff in self._dic.values():
            rv += f'{buff.path.relative_to(Path().cwd()) if buff.path else buff.cache_id}\t:\t{repr(buff)}\n'
        return rv

    def __iter__(self):
        for value in self._dic.values():
            yield value
    
    def __contains__(self, key):
        if self._make_key(key) in self._dic:
            return True
        return False

########## end of class _Cache ##########

class _Register:
    __slots__ = "dico"
    def __init__(self):
        self.dico = dict()

    def __str__(self):
        rv = str()
        for k,v in self.dico.items():
            rv += k +'\t:\t' + v.replace('\n', '\\n') + '\n'
        return rv

    def __getitem__(self, key):
        if isinstance(key, int):
            key = str(key)
        assert isinstance(key, str)
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
                self[str(k)] = self[str(k-1)]
            self["0"] = self['"']
            self.dico['"'] = value
        elif key.isupper():
            key = key.lower()
            self.dico[key] += value
            self['"'] = self.dico[key]
        elif key.islower():
            self.dico[key] = value
            self['"'] = self.dico[key]
        elif key.isnumeric() or key == '/':
            self.dico[key] = value
        elif key == '=':
            self.dico[key] = eval(value)
        elif key == '!':
            self.dico[key] = exec(value)

########## end of class _Register ##########

class _BoundNameSpace:
    def __init__(self, instance):
        super().__setattr__("_instance", instance) 

    def __setattr__(self, key, value):
        pass
            

    def __repr__(self):
        return self.__dict__.__repr__()

    def __iter__(self):
        return iter(self.__dict__)

########## end of _BoundNameSpace ##########

class _Actions:
    def __init__(self, instance):
        from vy.actions import __dict__ as action_dict
        self.insert = dict()
        self.command= dict()
        self.visual = dict()
        self.normal = dict()

        for name, action in action_dict.items():
            if callable(action) and not name.startswith('_'):
                final = partial(action, instance)

                final.atomic = action.atomic
                final.stand_alone = action.stand_alone
                final.with_args = action.with_args
                final.full = action.full
                final.__doc__ = action.__doc__ 

                if action.v_alias:
                    for k in action.v_alias:
                        self.visual[k]= final
                if action.n_alias:
                    for k in action.n_alias:
                        self.normal[k]= final
                if action.i_alias:
                    for k in action.i_alias: 
                        self.insert[k]= final
                if action.c_alias:
                    for k in action.c_alias: 
                        self.command[k]= final
                
########## end of class _Actions ##########

class Editor:
    """ This class is the data structure representing the state of the Vym editor.
    The editor class sould not need to be instanciated more than once.
    It is design to be self contained: if you want your code to interract with
    the editor, just pass the «editor» variable to your function.
    """    
    def __init__(self, *buffers, command_line=''):
        self.actions = _Actions(self)
        self.cache = _Cache()
        self.registr = _Register()
        self.screen = None # Wait to have a buffer before creating it.
        self.interface = Interface(self)
        self.command_line = command_line
        self._macro_keys = str()
        self._running = False
        self._work_stack = [self.cache[buff].path for buff in buffers]
        self.command_list = list()
        self.current_mode = ''
    
# TODO make read_stdin recognize escape chars, or maybe use a list instead of
# of a string ???
    def read_stdin(self):
        if self._macro_keys:
            rv = self._macro_keys[0]
            self._macro_keys = self._macro_keys[1:]
            return rv
        return get_a_key()
    
    def push_macro(self, string):
        assert isinstance(string, str)
        self._macro_keys = f'{string}{self._macro_keys}'
    
    def show_screen(self, renew=False, curbuf_queue=None):
        assert self._running
        screen = self.screen
        screen.infobar('( Screen Rendering )')
        try:
            if screen.needs_redraw or renew:
                screen.show(True)
            else:
                screen.show()
        except RuntimeError:
            raise 'Lexing is too Slow'
        screen.infobar(f' {self.current_mode.upper()} ', repr(self.current_buffer))

    def warning(self, msg):
        """Displays a warning message to the user. This should be the main way to cast
        information to the screen during the execution of a command as it allows the 
        user to enter the debugger if needed.
        In parts of the runtime where this method can't be reached, ( you don't have
        access to the editor variable ) you should raise an exception.
        """
        if self._macro_keys:
            print('this happened during the execution of a macro that is still running')
            print('left to evaluate: {self._macro_keys}')

        self.screen.minibar(f"{msg}\r\n\tpress any key to continue (or ^c to debug...)")
        key = get_a_key()
        if key == '\x03':
            print("\nyou are now in debugger. use 'up' to go back to the origin of this erros")
            print("'cont' to resume")
            breakpoint()

    def edit(self, location):
        """Changes the current buffer to edit location and set the interface
        accordingly.
        """
        if self.screen:
            self.current_window.change_buffer(self.cache[location])
            return
        self.screen = Screen(self.cache[location])
    
    @property
    def current_window(self):
        return self.screen.focused

    @property
    def current_buffer(self):
        return self.current_window.buff

    def __call__(self,buff=None, mode='normal'):
        """Calling the editor launches the command loop interraction."""
        if self._running is True:
            self.warning("You cannot interract with the editor stacking call to the «Editor» instance.")
            return
        self._running = True
        self.edit(buff if buff 
                    else self._work_stack.pop(0) if self._work_stack 
                    else None)

        self.screen.alternative_screen()
        self.screen.clear_screen()
        print('  Vy is starting. Please wait.')
        try:
            while True:
                try:
                    self.current_mode = mode if mode else self.current_mode
                    mode = self.interface(mode)
                except BdbQuit:
                    mode = 'normal'
                    continue
                    
                except Exception as exc:
                    self.screen.original_screen()
                    print('The following *unhandled* exception was encountered:\n  >  ' + repr(exc))
                    print('indicating:\n  >  ' + str(exc))
                    print()
                    print_tb(exc.__traceback__)
                    print()
                    print('The program may be corrupted, save all and restart quickly.')
                    try:
                        input('Press [ENTER] to resume  (or [CTRL+C] to close)')
                    except KeyboardInterrupt:
                        try:
                            input('\rPress [ENTER] to resume  (or [CTRL+C] (ONE MORE TIME) to close)')
                        except KeyboardInterrupt:
                            raise SystemExit
                    self.screen.alternative_screen()
                    mode = 'normal'
                    continue
                except SystemExit:
                    break
        finally:
            self._running = False
            self.screen.original_screen()
