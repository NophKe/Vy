"""This module contains the implementation of the «editor» class.

When importing Vy as a whole package, an instance of Editor is the only
thing you get. And when executing (python -m), an Editor *instance* shall
be the unique thing in the global dict.
"""

from pathlib import Path
from traceback import print_tb
from bdb import BdbQuit
#from functools import partial
from itertools import repeat, chain
from time import sleep, time, asctime
from threading import Thread
from queue import Queue

from vy.screen import Screen
from vy.interface import Interface
from vy.filetypes import Open_path
from vy.console import visit_stdin

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

########### end of class _Register ##########
#
#class _BoundNameSpace:
#    def __init__(self, instance):
#        super().__setattr__("_instance", instance) 
#    def __setattr__(self, key, value):
#        pass
#    def __repr__(self):
#        return self.__dict__.__repr__()
#    def __iter__(self):
#        return iter(self.__dict__)
########### end of _BoundNameSpace ##########

class _Actions:
    def __init__(self, instance):
        from vy.actions import __dict__ as action_dict
        self.insert = dict()
        self.command= dict()
        self.visual = dict()
        self.normal = dict()

        for name, action in action_dict.items():
            if callable(action) and not name.startswith('_'):
                if action.v_alias:
                    for k in action.v_alias:
                        self.visual[k]= action
                if action.n_alias:
                    for k in action.n_alias:
                        self.normal[k]= action
                if action.i_alias:
                    for k in action.i_alias: 
                        self.insert[k]= action
                if action.c_alias:
                    for k in action.c_alias: 
                        self.command[k]= action
                
########## end of class _Actions ##########

class _Editor:
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
        self._async_io_flag = False
        self._work_stack = [self.cache[buff].path for buff in buffers]
        self.command_list = list()
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
        """Displays a warning message to the user. This should be the main way to cast
        information to the screen during the execution of a command as it allows the 
        user to enter the debugger if needed.
        In parts of the runtime where this method can't be reached, ( you don't have
        access to the editor variable ) you should raise an exception.
        """
        if self._macro_keys:
            self.screen.minibar_completer(
             'this happened during the execution of a macro that is still running',
             f'left to evaluate: {self._macro_keys}')
        self.screen.minibar(*msg.splitlines(), '\tpress any key to continue')
        self.read_stdin()
        self.screen.minibar('')
        self.screen.minibar_completer()

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
            buffer = self.cache[location]
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

    def print_loop(self):
        flash_screen = False # do not require lock
        old_screen = list()  
        last_print = time()
        infobar = self.screen.infobar
        stop = False

        while self._async_io_flag:
            if stop:
                self._input_queue.join()
                stop = False
                continue
            tasks = self._input_queue.qsize()
            delta = (start := time()) - last_print

            if delta > 5:               # if screen is more than 5 seconds late
                stop = True             # draw it noexcept one last time
                flash_screen = False
                infobar(f' ___ SCREEN DISABLED ___ ', f'  {asctime()}  ')
            elif delta > 1:
                while time() - start < 0.33:
                    if not self._input_queue.qsize():
                        break           # if screen is more than one second late
                    sleep(0.04)         # miss a frame as long as there are keystrokes
                flash_screen = False    # to read, but draw it noexcept. 
                infobar(f' ___ SCREEN RENDERING ___ ', f'last good screen {round(time() - last_print,2)} seconds ago')

            elif delta < 0.04:
                sleep(0.04 - delta)     # Never try more than 25 fps
                continue

            elif tasks:                 # if job to do spend this frame waiting
                start = time()          # for it to complete
                while time() - start < 0.04:
                    if not self._input_queue.qsize():
                        break
                    sleep(0.0001)
                flash_screen = True
                infobar(f' {self.current_mode.upper()} ', repr(self.current_buffer))

            else:                        # nothing to do. Draw screen synchronously.
                infobar(f' {self.current_mode.upper()} ', repr(self.current_buffer))
                flash_screen = False

            try:
                new_screen = self.screen.get_line_list(flash_screen)
            except RuntimeError:
                if flash_screen:
                    continue
                raise

            filtered = list()
            for index, (line, old_line) in enumerate(
            zip(new_screen, chain(old_screen, repeat(''))),start=1):
                if line != old_line:
                    filtered.append(f'\x1b[{index};1H{line}')

            old_screen = new_screen
            print(''.join(filtered), end='', flush=True)

            if ((not flash_screen and not tasks) or 
               ((0.04 < delta < 0.33) and (new_screen == old_screen))):
                    last_print = time()


    def input_loop(self):
        stdin_reader = visit_stdin()
        while self._async_io_flag:
            key_press = next(stdin_reader) 
            if key_press:
                self._input_queue.put(key_press)
            #sleep(0)
        del stdin_reader # help garbage collector

    def start_async_io(self):
        assert not self._async_io_flag
        if not DEBUG:
            self.screen.alternative_screen()
            self.screen.clear_screen()
            self.screen.hide_cursor()
        self._async_io_flag = True
        self.input_thread = Thread(target=self.input_loop,)
        self.print_thread = Thread(target=self.print_loop,)
        self.input_thread.start()
        self.print_thread.start()

    def stop_async_io(self):
        assert self._async_io_flag
        self._async_io_flag = False
        self.print_thread.join()
        self.input_thread.join()
        if not DEBUG:
            self.screen.original_screen()
            self.screen.show_cursor()
        #self._input_queue.join()

        
    def __call__(self, buff=None, mode='normal'):
        """
        Calling the editor launches the command loop interraction.

        If the editor is allready running it is equivalent to Editor.edit(filename)
        (Changes the current buffer and current window to edit location)

        """
        if self._running:
            return self.edit(buff)
        self._running = True

        self.edit(buff if buff 
                    else self._work_stack.pop(0) if self._work_stack 
                    else None)
        self.start_async_io()
        try:
            while True:
                try:
                    self.current_mode = mode if mode else self.current_mode
                    mode = self.interface(mode)
                except BdbQuit:
                    mode = 'normal'
                    continue
                except Exception as exc:
                    self.stop_async_io()
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
