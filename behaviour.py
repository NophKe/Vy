"""
This module contains classes that are meant to be inherited 
by the final implementations of «filetypes».
"""

from .interface.helpers import do
from .actions import *
from . import keys as k
from .filetypes.motions import motion as motion_dict
from collections import ChainMap
from pathlib import Path

class VyPath:
    def __get__(self, inst, objtype=None):
        return inst._path
    def __set__(self, inst, value):
        assert isinstance(value, (str, Path, type(None)))
        if value is None:
            inst._path = None
        elif isinstance(value, str):
            inst._path = Path(value).resolve()
        elif isinstance(value, Path):
            inst._path = value.resolve()

class VyString:
    def __get__(self, inst, objtype=None):
        return inst._string
    def __set__(self, inst, value):
        assert isinstance(value, str)
        inst.set_undo_point()
        inst._string = value
        if inst.redo_list:
            inst.redo_list = list()

class Behaviour:
    """Abstract Behaviour class"""
    stand_alone_commands = {}
    full_commands = {}
    motion_commands = {}
    string = VyString()
    path = VyPath()

    def __init_subclass__(cls):
        """The is of this function is to let any implementation override
        the three dicts, but joining them anyway in the final class.
        """
        for klass in cls.mro():
            if hasattr(klass, 'stand_alone_commands'):
                cls.stand_alone_commands.update(klass.stand_alone_commands)
            if hasattr(klass, 'full_commands'):
                cls.full_commands.update( klass.full_commands)
            if hasattr(klass, 'motion_commands'):
                cls.motion_commands.update( klass.motion_commands)


class BaseBehaviour(Behaviour):          
    """Base Class, if any of the action in the dicts of this class
    implements an action that may be unavailable to all file types,
    it must implement any necessary abstract method and properties
    that the current buffer would need."""
    def save_as(self):
        """ Bogus implemetation."""
    def save(self):
        """ Bogus implemetation."""
    @property
    def unsaved(self):
        """ Bogus implemetation."""
        return False

    stand_alone_commands = {
# windows manipulation
        k.C_L           : lambda ed, cmd: ed.screen.show(True),
        k.C_W + k.left  : DO_focus_right_window,
        k.C_W + k.C_H   : DO_focus_left_window,
        k.C_W + 'h'     : DO_focus_left_window,
        
        k.C_W + k.right : DO_focus_right_window,
        k.C_W + k.C_L   : DO_focus_right_window,
        k.C_W + 'l'     : DO_focus_right_window,
        
        k.C_W + 'o'     : DO_keep_only_current_window,
        k.C_W + k.C_O   : DO_keep_only_current_window,

        k.C_W + k.C_V   : DO_vsplit,
        k.C_W + 'v'     : DO_vsplit,
        k.C_W + 'V'     : DO_vsplit,
# recenter
        'zz'    : DO_zz,
        'zt'    : DO_zt,
        'zb'    : DO_zb,
# other modes
        ':'     : lambda ed, cmd: 'command',
# leave
        'ZZ'    : do( DO_try_to_save, DO_exit_nice),
        'ZQ'    : DO_force_leave_current_window,
# misc
#       '?'     : lambda x, arg: x.warning(f'{x.current_buffer.cursor_lin_col = }'),
    }

class ReadOnlyText(BaseBehaviour):
    stand_alone_commands = {
        '/'     : lambda ed, cmd: 'search_forward',
        '?'     : lambda ed, cmd: 'search_backward',
    # page scrolling 
        k.page_up   : DO_page_up,
        k.page_down : DO_page_down,}
    
    full_commands = {
        'n'     : DO_normal_n,
    }
    
    motion_commands = ChainMap(motion_dict, {
    # control + Arrow
        k.C_left  : 'b',
        k.C_right : 'w',
    # shift + Arrow
        k.S_left  : 'b',
        k.S_right : 'w',
    # arrows
        k.left  : 'h',
        k.right : 'l',
        k.up    : 'k',
        k.down  : 'j',
    # asking input
        'f' : DO_f,
    # other
        ' '     : 'l',
        '\r'    : 'j', })

GO = lambda where: lambda ed, cmd: ed.current_buffer.move_cursor(where)

class WritableText(ReadOnlyText):
    """The behaviour of a «standard» text file buffer."""

    stand_alone_commands = {
        'p' : DO_paste,
# goto insert_mode
        'i'   : lambda ed, cmd: 'insert',
        'I'   : do( GO('0'), mode='insert'),
        'o'   : do( GO('$'), r"x.current_buffer.insert('\n')", mode='insert'),
        'O'   : do( GO('0'), r"x.current_buffer.insert('\n')", GO('k'), mode='insert'),
        'a'   : do( GO('l'), mode='insert'),
        'A'   : do( GO('$'), mode='insert'),
        k.insert    : do(mode='insert'),
# misc
        k.C_R   : lambda ed, cmd: ed.current_buffer.redo(),
        'u'     : lambda ed, cmd: ed.current_buffer.undo(),

# edition
        k.suppr : 'x',
        'D' : lambda ed, cmd: ed.current_buffer.__delitem__('cursor:$'),
        'x' : DO_suppr,
        'X' : lambda ed, cmd: ed.current_buffer.backspace(),
        '~' : DO_normal_tilde, 

# sub-modes
        'r' : DO_r,
       }
       
    full_commands = {
        'y' : yank,
        'd' : delete,
        'g~'    : swap_case
    }

