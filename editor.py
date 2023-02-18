"""This module contains the implementation of the «editor» class.

When importing Vy as a whole package, an instance of Editor is the only
thing you get. And when executing (python -m), an Editor *instance* shall
be the unique thing in the global dict.
"""

from pathlib import Path
from traceback import print_tb
from bdb import BdbQuit
from itertools import repeat, chain
from time import sleep, time
from threading import Thread
from queue import Queue

from vy.screen import Screen
from vy.interface import Interface
from vy.filetypes import Open_path
from vy.console import getch_noblock
from vy.global_config import DEBUG

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
    __slots__ = ("_dic", "_counter")
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
        else:
            new_buffer = Open_path(key)
            assert new_buffer is not None
            self._dic[key] = new_buffer
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
        raise TypeError(f"key is type:{key.__class__}, int, str, or Path expected")

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
        yield from self._dic.values()    

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
            if key in self.dico:
                self.dico[key] += value
            else:
                self.dico[key] = value
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

        else:
            raise RuntimeError

class NameSpace:
    def __init__(self):
        self.insert = dict()
        self.command= dict()
        self.visual = dict()
        self.normal = dict()


class _Editor:
    """ This class is the data structure representing the state of the Vym editor.
    The editor class sould not need to be instanciated more than once.
    It is design to be self contained: if you want your code to interract with
    the editor, just pass the «editor» variable to your function.
    """    

    def _init_actions(self):
        from vy.actions import __dict__ as action_dict

        actions = NameSpace()

        for name, action in action_dict.items():
            if callable(action) and not name.startswith('_'):
                if action.v_alias:
                    for k in action.v_alias:
                        actions.visual[k]= action
                if action.n_alias:
                    for k in action.n_alias:
                        actions.normal[k]= action
                if action.i_alias:
                    for k in action.i_alias: 
                        actions.insert[k]= action
                if action.c_alias:
                    for k in action.c_alias: 
                        actions.command[k]= action
        self.actions = actions

    def __init__(self, *buffers, command_line=''):
        self._init_actions()
        #self.actions = _Actions(self)
        self.cache = _Cache()
        self.registr = _Register()
        self.screen = None # Wait to have a buffer before creating it.
        self.interface = Interface(self)
        self.command_line = command_line
        self._macro_keys = str()
        self._running = False
        self._async_io_flag = False
        self._work_stack = [self.cache[buff].path for buff in buffers]
        #self.command_list = list()
        self.current_mode = ''
        self._input_queue = Queue()
    
    def read_stdin(self):
        if self._macro_keys:
            rv = self._macro_keys[0]
            self._macro_keys = self._macro_keys[1:]
            return rv
        key_press = self._input_queue.get(block=True)
        self._input_queue.task_done()
        return key_press


    def push_macro(self, string):
        assert isinstance(string, str)
        self._macro_keys = f'{string}{self._macro_keys}'

    def warning(self, msg):
        """
        Displays a warning message to the user. This should be the main way 
        to cast information to the screen during the execution of a command 
        as it allows the user to enter the debugger if needed.
        In parts of the runtime where this method can't be reached,
        ( you don't have access to the editor variable ) you should raise an 
        exception.
        """
        if self._macro_keys:
            self.screen.minibar_completer(
              'this happened during the execution of a macro that is still running',
              f'left to evaluate: {self._macro_keys}')
        self.screen.minibar(*msg.splitlines(), '\tpress any key to continue')
        self.read_stdin()
        self.screen.minibar('')
        self.screen.minibar_completer.give_up()

    def edit(self, location):
        """
        Changes the current buffer to edit location and set the interface accordingly.
        """
        try:
            buffer = self.cache[location]
        except UnicodeDecodeError:
            self.warning(f"Vy cannot deal with encoding of file {location}")
        except PermissionError:
            self.warning(f"You do not seem to have enough rights to read {location}")
        else:
            if self.screen:
                self.current_window.change_buffer(buffer)
            else:
                self.screen = Screen(buffer)
    
    @property
    def current_window(self):
        return self.screen.focused

    @property
    def current_buffer(self): 
        return self.screen.focused.buff

### TODO -- move this fonction to screen module
###
### - replace self._asyncio_flag by a threading.Condition
###
    def print_loop(self):
        old_screen = list()
        infobar = self.screen.infobar
        missed = 0
        ok_flag = True
        get_line_list = self.screen.get_line_list
        left_keys = self._input_queue.qsize
        start = time()

        while self._async_io_flag:
            sleep(0.04) # cant try more than  25fps
            if time() - start > 5:
                old_screen = []
                start = time()

            if ok_flag and not left_keys() > 1:
                infobar(f' {self.current_mode.upper()} ', repr(self.current_buffer))
            else:
                infobar(' ___ SCREEN OUT OF SYNC -- STOP TOUCHING KEYBOARD___ ',
                f'Failed: {missed} time(s), '
                f'waiting keystrokes: {self._input_queue.qsize()}')

            new_screen, ok_flag = get_line_list()

            filtered = ''
            for index, (line, old_line) in enumerate(
                            zip(new_screen, chain(old_screen, repeat(''))),start=1):
                if line != old_line and line:
                    filtered += f'\x1b[{index};1H{line}'

            print(filtered, end='\r', flush=True)

            missed = missed + 1 if not ok_flag else 0
            if ok_flag:
                old_screen = new_screen

    def input_loop(self):
        for key_press in getch_noblock():
            if not self._async_io_flag:
                break
            elif not key_press:
                continue
            self._input_queue.put(key_press)

    def start_async_io(self):
        assert not self._async_io_flag
        if not DEBUG:
            self.screen.alternative_screen()
            self.screen.clear_screen()
        self.screen.hide_cursor()
        self._async_io_flag = True
        self.input_thread = Thread(target=self.input_loop)
        self.print_thread = Thread(target=self.print_loop,)
        self.input_thread.start()
        self.print_thread.start()

    def stop_async_io(self):
        self._async_io_flag = False
        self.input_thread.join()
        self.print_thread.join()
        if not DEBUG:
            self.screen.clear_screen()
            self.screen.original_screen()
        self.screen.show_cursor()
        #assert self._input_queue.join() ## one key may get stuck there
        #                                ## what can we do ?
        
    def __call__(self, buff=None, mode='normal'):
        """
        Calling the editor launches the command loop interraction.
        If the editor is allready running it is equivalent to Editor.edit(filename)
        """
        if self._running:
            return self.edit(buff)

        try:
            self.edit(buff if buff 
                        else self._work_stack.pop(0) if self._work_stack 
                        else None)

            self.start_async_io()
            self._running = True

            while True:
                try:
                    self.current_mode = mode if mode else self.current_mode
                    mode = self.interface(mode)
                except BdbQuit:
                    self.start_async_io()
                    mode = 'normal'
                    continue
                except Exception as exc:
                    self.stop_async_io()
                    print(self.screen.infobar_txt)
                    print(  'The following *unhandled* exception was encountered:\n  >  ' + repr(exc),
                            'indicating:\n  >  ' + str(exc) + '\n')
                    print_tb(exc.__traceback__)
                    print('\nThe program may be corrupted, save all and restart quickly.')
                    try:
                        input('Press [ENTER] to resume  (or [CTRL+C] to close)')
                    except KeyboardInterrupt:
                        return 1
                    mode = 'normal'
                    self.start_async_io()
                    continue
        finally:
            self._running = False
            self.stop_async_io()
            return 0 # exit_code
