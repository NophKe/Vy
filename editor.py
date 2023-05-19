"""
This module contains the implementation of the «editor» class.

There should be no reason for instanciating the _Editor class.  When
importing Vy as a package, use the vy() facility function to lauch the
editor.  And when executing (python -m), an Editor *instance* is
allready present in the global dict.

The Editor singleton instance you want to interract with belong to the
__main__ module of the package.  There should be no reason to use any of
the classes defined in this module directly.
"""

from pathlib import Path
from traceback import print_tb
from bdb import BdbQuit
from pdb import post_mortem
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
    """
    Simple wrapper around a dict that lets you index a buffer by its
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
        an int, None or any allready visited buffer. 

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
        try:
            return self._dic[(key := self._make_key(key))]
        except KeyError:
            new_buffer = Open_path(key)
            self._dic[key] = new_buffer
            new_buffer.cache_id = key
            return new_buffer

    #@staticmethod
    def _make_key(self, key):
        if hasattr(key, 'cache_id'):
            return key.cache_id
        elif isinstance(key, int):
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
        from pprint import pformat
        return pformat(self._dic)

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
    valid_registers  = ( 'abcdefghijklmnopqrstuvwxyz'
                         'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                         '>+-*/.:%#"=!0123456789')
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
        assert key in self.valid_registers
        try:
            return self.dico[key]
        except KeyError:
            return ''

    def __setitem__(self, key, value):
        if isinstance(key, int):
            key = str(key)
        assert isinstance(key, str)
        assert key in self.valid_registers

        if key == '_':
            return
        
        elif key in ':.>':
            self.dico[key] = value

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
    __slots__ = ('insert', 'command', 'visual', 'normal', 'motion')
    def __init__(self):
        self.insert = dict()
        self.command= dict()
        self.visual = dict()
        self.normal = dict()
        self.motion = dict()

class _Editor:
    """ This class is the data structure representing the state of the Vym editor.
    The editor class sould not need to be instanciated more than once.
    It is design to be self contained: if you want your code to interract with
    the editor, just pass the «editor» variable to your function.
    """    

    def _init_actions(self):
        from vy.actions import __dict__ as action_dict
        actions = NameSpace()
        try:
            for name, action in action_dict.items():
                if callable(action) and not name.startswith('_'):
                    if action.v_alias:
                        for k in action.v_alias:
                            actions.visual[k]= action
                    if action.n_alias:
                        if action.motion:
                            for k in action.n_alias:
                                actions.normal[k]= action
                                actions.motion[k]= action
                                actions.visual[k]= action
                        else:
                            for k in action.n_alias:
                                actions.normal[k]= action
                    if action.i_alias:
                        for k in action.i_alias: 
                            actions.insert[k]= action
                    if action.c_alias:
                        for k in action.c_alias: 
                            actions.command[k]= action
            self.actions = actions
        except:
            print('error during Editor initialisation')
            print(f'{action = }, {name = }, {action.__module__ = }')
            raise

    def __init__(self, *buffers, command_line=''):
        self.jump_list = []
        self.jump_list_pointer = -1
        self._init_actions()
        #self.actions = _Actions(self)
        self.cache = _Cache()
        self.registr = _Register()
        self.screen = None # Wait to have a buffer before creating it.
        self.interface = Interface(self)
        self.command_line = command_line
        self._macro_keys = []
        self._running = False
        self._async_io_flag = False
        self.arg_list = [self.cache[buff].path for buff in buffers]
        self.arg_list_pointer = 0
        #self.command_list = list()
        self.current_mode = ''
        self._input_queue = Queue()
        
    def save_in_jump_list(self):
        curbuf = self.current_buffer
        lin, col = curbuf.cursor_lin_col
        try:
            last_buf, last_lin, last_col = self.jump_list[-1]
        except IndexError:
            self.jump_list.append((curbuf, lin, col))
        else:
            if last_buf is curbuf and (last_lin == lin or last_col == col):
                return
            self.jump_list.append((curbuf, lin, col))
    
    def read_stdin(self):
        if self._macro_keys:
            return self._macro_keys.pop(0)
        key_press = self._input_queue.get(block=True)
        self._input_queue.task_done()
        return key_press
    
    def visit_stdin(self):
        rv = self.read_stdin()
        self.push_macro(rv)
        return rv

    def push_macro(self, string):
        assert isinstance(string, str)
        self._macro_keys.insert(0, string)

    def warning(self, msg):
        """
        Displays a warning message to the user. This should be the main way 
        to cast information to the screen during the execution of a command 
        as it allows the user to enter the debugger if needed.
        In parts of the runtime where this method can't be reached,
        ( you don't have access to the editor variable ) you should raise an 
        exception.
        """
        if not self._running:
            print(msg)
            return
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
            self.warning(f"You do not seem to have enough rights to read {location}\n"
                          "or the targeted directory does not exist")
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
### - replace self._asyncio_flag by a threading.Condition ?
###
    def print_loop(self):
        old_screen = list()
        infobar = self.screen.infobar
        missed = 0
        ok_flag = True
        get_line_list = self.screen.get_line_list
        left_keys = self._input_queue.qsize
        start = 0
        filtered = ''
        new_screen = list()
        old_screen = list()

        while self._async_io_flag:
            try:
                sleep(0.04)             # do not try more than  25fps
                if ((now := time()) - start) > 10: # and force redraw every 10 seconds
                    self.screen._last = None
                    old_screen = []
                    start = now

                if ok_flag and not left_keys() > 1:
                    self.screen.infobar(f' {self.current_mode.upper()} ', repr(self.current_buffer))
                    pass
                else:
                    sleep(0.1)
                    self.screen.infobar(' ___ SCREEN OUT OF SYNC -- STOP TOUCHING KEYBOARD___ ',
                    f'Failed: {missed} time(s), '
                    f'waiting keystrokes: {self._input_queue.qsize()}')

                new_screen, ok_flag = get_line_list()

                filtered = ''
                for index, (line, old_line) in enumerate(
                                zip(new_screen, chain(old_screen, repeat(''))),
                                start=1):
                    if line != old_line:
                        filtered += f'\x1b[{index};1H{line}'

                if filtered:
                    print(filtered, end='\r', flush=True)

                if ok_flag:
                    missed = 0
                    old_screen = new_screen
                else:
                    missed + 1
            except BaseException as exc:
                import traceback
                infos = traceback.format_exc().replace('\n', '\r\n')
                self.screen.original_screen()
                self.screen.show_cursor()
                print( 'Editor.print_thread crashed ! ')
                print(  'The following *unhandled* exception was encountered:\r\n'
                       f'  >  {repr(exc)} indicating:\r\n'
                       f'  >  {str(exc)}\r\n'
                       f'{infos}\r\n'
                        '(you have to quit blindly or repair live.)')

    def input_loop(self):
        reader = getch_noblock()
        for key_press in reader:
            if self._async_io_flag:
                if key_press:
                    self._input_queue.put(key_press)
            else:
                del reader
                break

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
        If the editor is allready running it is equivalent to Editor.edit()
        """
        if self._running:
            return self.edit(buff)

        if buff:
            self.edit(buff)
        elif self.arg_list:
            self.edit(self.arg_list[self.arg_list_pointer])
        else:
            self.edit(None)

        try:
            self.start_async_io()
            self._running = True
            self.current_mode = mode

            while True:
                try:
                    self.current_mode = self.interface(self.current_mode) \
                                        or self.current_mode
                    continue
                except SystemExit:
                    raise
                except BaseException as exc:
                    import sys
                    type_, value_, trace_ = sys.exc_info()
                    self.stop_async_io()
                    print(self.screen.infobar_txt)
                    print(  'The following *unhandled* exception was encountered:\n'
                           f'  >  {repr(exc)} indicating:\n'
                           f'  >  {str(exc)}\n')
                    print_tb(exc.__traceback__)
                    print('\nThe program may be corrupted, save all and restart quickly.')
                    try:
                        input(('Press [ENTER] to try resuming\n'
                               'or    [CTRL+C] to close immediatly\n'
                               'or    [CTRL+D] to start debugger\n\r\t'))
                    except EOFError:
                        self.screen.original_screen()
                        try:
                            post_mortem(trace_)
                        except BdbQuit:
                            pass
                    except KeyboardInterrupt:
                        return 1
                    self.current_mode = 'normal'
                    self.start_async_io()
                    continue
        finally:
            self._running = False
            self.stop_async_io()
        return 0 # exit_code
