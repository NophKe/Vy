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
from bdb import BdbQuit
from itertools import repeat, chain
from time import sleep, time
from threading import Thread, Lock
from queue import Queue
from signal import signal, SIGWINCH

from vy.screen import Screen
from vy.interface import Interface
from vy.filetypes import Open_path
from vy.console import getch_noblock
from vy.utils import _HistoryList
from vy.clipboard import _Register
from vy.global_config import DEBUG
from vy import keys

class _Cache:
    """
    Simple wrapper around a dict that lets you index a buffer by its
    internal id, or any relative or absolute version of its path. use:

    >>> x = Cache()
    >>> x['/home/Nono/test.txt']
    TextFile('/home/Nono/test.txt')
    >>> x['/home/Nono/test.txt'] is x['./test.txt']
    True
    >>> del x['test.txt']
    >>> '../nono/test.txt' in x
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
            return self._dic[(key :=self._make_key(key))]
        except KeyError:
            new_buffer = Open_path(key)
            self._dic[key] = new_buffer
            new_buffer.cache_id = key
            return new_buffer

    @staticmethod
    def _make_key(key):
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

    def __iter__(self):
        yield from self._dic.values()    

    def __contains__(self, key):
        return self._make_key(key) in self._dic

########## end of class _Cache ##########

class ActionDict(dict):
    __slots__ = 'instance'
    def __init__(self, instance):
        self.instance = instance
    def __call__(self, value, **kwargs):
        return self[value](self.instance, **kwargs)
    
class NameSpace:
    __slots__ = ('insert', 'command', 'visual', 'normal', 'motion')
    def __init__(self, instance):
        self.insert = ActionDict(instance)
        self.command= ActionDict(instance)
        self.visual = ActionDict(instance)
        self.normal = ActionDict(instance)
        self.motion = ActionDict(instance)

class _Editor:
    """ The data structure representing the editor's state.
    The _Editor class should not need to be instanciated more than once.
    It is design to be self-contained: if you want your code to interract with
    the editor, just pass the «editor» variable to your function.
    
    """    
    class MustGiveUp(Exception):
        pass

    class NewInfo(Exception):
        pass

    def _init_actions(self):
        from vy.actions import __dict__ as action_dict
#        from vy.actions.mode_change import normal_mode
        actions = NameSpace(self)
        try:
            for name, action in action_dict.items():
            
#                if action is normal_mode:
#                    assert action.v_alias
# 
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
        self.cache = _Cache()
        self.jump_list = _HistoryList()
        self.interface = Interface(self)
        # From arguments        
        self.command_line = command_line
        self.arg_list = [self.cache[buff].path for buff in buffers]
        self.arg_list_pointer = 0
        
        self._init_actions()
        self.registr = _Register()
        self.screen = None # Wait to have a buffer before creating it.
        self._macro_keys = []
        self._running = False
        self._async_io_flag = False
        self.macros = {}
        self.record_macro = ''
        self.current_mode = ''
        self._input_queue = Queue()
        self._skip_next_undo = False
        self._screen_lock = Lock()
        
    def save_undo_record(self):
        if self._skip_next_undo:
            raise Error
            self._skip_next_undo = False
        else:
            self.current_buffer.set_undo_point()
        
    def save_in_jump_list(self):
        curbuf = self.current_buffer
        lin, col = curbuf.cursor_lin_col
        try:
            last_buf, last_lin, last_col = self.jump_list.last_record()
        except IndexError:
            self.jump_list.append((curbuf, lin, col))
        else:
            if (last_buf is curbuf) and ((last_lin == lin) or (last_col == col)): 
                pass
            else:
                self.jump_list.append((curbuf, lin, col))
    
    def read_stdin(self):
        if self._macro_keys:
            return self._macro_keys.pop(0)
        key_press = self._input_queue.get(block=True)
        if self.record_macro:
            try:
                self.macros[self.record_macro].append(key_press)
            except KeyError:
                self.macros[self.record_macro] = [key_press]
        self._input_queue.task_done()
        return key_press
    
    def visit_stdin(self):
        rv = self.read_stdin()
        self.push_macro(rv)
        return rv

    def push_macro(self, string):
        assert isinstance(string, str)
        self._macro_keys.insert(0, string)

    def confirm(self, msg):
        if not self._running or not self._async_io_flag:
            print(msg)
            if self._macro_keys:
                self.screen.minibar_completer(
                  'this happened during the execution of a macro that is still running',
                  f'left to evaluate: {self._macro_keys}')
            if input('(press any key)') != keys.CR:
                raise self.MustGiveUp
                
        self.screen.minibar(*msg.splitlines(), 
                            '    ( press enter to confirm, anything else to skip. )')
        
        answer = self.read_stdin() 
        self.screen.minibar('')
        self.screen.minibar_completer.give_up()
        if answer != keys.CR:
            raise self.MustGiveUp
        
    def warning(self, msg):
        """
        Displays a warning message to the user. This should be the main way 
        to cast information to the screen during the execution of a command 
        as it allows the user to enter the debugger if needed.
        In parts of the runtime where this method can't be reached,
        ( you don't have access to the editor variable ) you should raise an 
        exception.
        """
        if not self._running or not self._async_io_flag:
            print(msg)
            input('(______________________press any key)')
            return
        if self._macro_keys:
            self.screen.minibar_completer(
              'this happened during the execution of a macro that is still running',
              f'left to evaluate: {self._macro_keys}')
        self.screen.minibar(*msg.splitlines(), '    ( press any key to continue )')
        self.read_stdin()
        self.screen.minibar('')
        self.screen.minibar_completer.give_up()

    def edit(self, location, position=0):
        """
        Changes the current buffer to edit location and set the interface accordingly.
        """
        try:
            buffer = self.cache[location]
        except UnicodeDecodeError:
            raise self.MustGiveUp(f"Vy cannot deal with encoding of file {location}")
        except PermissionError:
            raise self.MustGiveUp(f"You do not seem to have enough rights to read {location}\n"
                          "or the targeted directory does not exist")

        if self.screen:
            self.current_window.change_buffer(buffer)
        else:
            self.screen = Screen(buffer)
        buffer.cursor = position
        return buffer

    @property
    def current_window(self):
        return self.screen.focused

    @property
    def current_buffer(self): 
        return self.screen.focused.buff

    def print_loop(self):
        from vy.utils import async_update
        
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
        error = 'editor initialising'
        

        while self._async_io_flag:
            sleep(0.04)             # do not try too much
            if not self._async_io_flag:
                break
                
            if ((now := time()) - start) > 5: # and force redraw sometimes
                old_screen.clear()
                start = now

            with self._screen_lock:
                if ok_flag and not left_keys(): # > 1:
                    self.screen.recenter()
                    self.screen.infobar(f' {self.current_mode.upper()} ', 
                                        f'recording macro: {self.record_macro}' if self.record_macro else 
                                        f'waiting keystrokes: {left_keys():3}' if left_keys() else
                                        '' )
                else:
                    sleep(0.1)
                    self.screen.infobar(' ___ SCREEN OUT OF SYNC -- STOP TOUCHING KEYBOARD___ ',
                                        f'Failed: {missed:3} time(s), waiting keystrokes: {left_keys():3}, {error= :4} ' )

                new_screen, ok_flag, error = get_line_list()
    
            filtered = ''
            for index, (line, old_line) in enumerate(
                            zip(new_screen, chain(old_screen, repeat(''))),
                            start=1):
                if line and line != old_line:
                    filtered += f'\x1b[{index};1H{line}'

            if filtered:
                print(filtered, end='\r', flush=True)

            if ok_flag:
                missed = 0
                old_screen = new_screen
            else:
                missed += 1

    def input_loop(self):
        reader = getch_noblock()
        for key_press in reader:
            if self._async_io_flag:
                if key_press:
                    if key_press == keys.F12:
                        from __main__ import dump_traceback
                        dump_traceback() 
                    self._input_queue.put(key_press)
            else:
                break
        del reader

    def start_async_io(self):
#        signal(SIGWINCH, lambda x, y: self.screen.set_redraw_needed())
        from vy.global_config import BG_COLOR
        assert not self._async_io_flag

        if not DEBUG:
            self.screen.alternative_screen()
            self.screen.clear_screen()
        self.screen.hide_cursor()
        self.screen.enable_bracketed_paste()
        self.screen.enable_mouse_tracking()
        self._async_io_flag = True
        
        print('\x1b[48:5:234m', flush=True)
        
        self.input_thread = Thread(target=self.input_loop)
        self.print_thread = Thread(target=self.print_loop,)
        self.input_thread.start()
        self.print_thread.start()

    def stop_async_io(self):
        if self._async_io_flag:
            self._async_io_flag = False
            self.input_thread.join()
            self.print_thread.join()
 
        if not DEBUG:
            self.screen.clear_screen()
            self.screen.original_screen()
            self.screen.show_cursor()
            self.screen.disable_bracketed_paste()
            self.screen.disable_mouse_tracking()
            self.screen.bottom()
            self.screen.reset()
            
        print('\x1b[0m')
            #assert self._input_queue.join() ## one key may get stuck there
            #                                ## what can we do ?
        
    def __call__(self, buff=None, mode='normal', position=0):
        """
        Calling the editor launches the command loop interraction.
        If the editor is allready running it is equivalent to Editor.edit()
        """
        if self._running:
            return self.edit(buff, position)

        try:
            import gc
            gc.collect()
            gc.freeze()
        except:
            # we're probably not on cpython, just
            pass 

        if buff:
            self.edit(buff, position)
        elif self.arg_list:
            self.edit(self.arg_list[self.arg_list_pointer])
        else:
            self.edit(None)

        try:
            self.start_async_io()
            self._running = True
            self.screen.minibar('Welcome to Vy.   (type :h to get help)')
            self.current_mode = mode

            while True:
                try:
                    self.current_mode = self.interface(self.current_mode) \
                                        or self.current_mode
                    self.save_in_jump_list()
                    self.save_undo_record()
#                    self.recenter_screen()
                    continue
                
                except self.MustGiveUp as exc:
                    msg = str(exc)
                    if msg:
                        self.warning(msg)
                    # don't save undo list, or position, or anything   
                    continue

                except self.NewInfo as exc:
                    self.screen.minibar(str(exc))
                    continue
                
                except BdbQuit:
                    pass
                    
                except Exception as exc:
                    from traceback import print_tb
                    self.stop_async_io()
                    
                    self.screen.underline()
                    print('The following *unhandled* exception was encountered:')
                    self.screen.reset()
                    self.screen.bold()
                    
                    print(f'  >  {repr(exc)} indicating:')
                    print(f'  >  {str(exc)}')
                    self.screen.reset()
                    
                    print()
                    print_tb(exc.__traceback__)
                    self.screen.reset()
                    print()
                    
                    print('The program may be corrupted, save all and restart quickly.')
                    try:
                        input(('Press [ENTER] to try resuming \n'
                               'or    [CTRL+C] to close immediatly \n'
                               'or    [CTRL+D] to start debugger \n\r\t'))
                    except EOFError:
                        from pdb import post_mortem
                        self.screen.original_screen()
                        post_mortem(exc.__traceback__)
                        
                    except KeyboardInterrupt as exc:
                        raise exc from None
                        
                self.current_mode = 'normal'
                self.start_async_io()
                continue
        finally:
            self._input_queue.shutdown(immediate=True)
            self._running = False
            self.stop_async_io()
            self.registr.save()
        return 0 # exit_code
