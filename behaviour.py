"""
This module contains classes that are meant to be inherited 
by the final implementations of «filetypes».
"""
from .interface.helpers import do
from .actions import *
from . import keys as k
from .filetypes.motions import motion as motion_dict
from collections import ChainMap

class Behaviour:
    """Abstract Behaviour class"""
    stand_alone_commands = {}
    full_commands = {}
    motion_commands = {}

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

    # those next attrs/props shoud be soon replaced by abstract items.
    def stop_undo_record(self):
        """ NOT IMPLEMENTED """
    def start_undo_record(self):
        """ NOT IMPLEMENTED """
    def set_undo_point(self):
        """ NOT IMPLEMENTED """
    def save_as(self):
        """ NOT IMPLEMENTED """
    def save(self):
        """ NOT IMPLEMENTED """
    @property
    def unsaved(self):
        """ NOT IMPLEMENTED """
        return False
    @property
    def string(self):
        """ NOT IMPLEMENTED """
        return self._string
    

class BaseBehaviour(Behaviour):          
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
        ':'     : do(mode='command'),
# leave
        'ZZ'    : do( DO_try_to_save, DO_exit_nice),
        'ZQ'    : DO_force_leave_current_window,
# misc
        '?'     : lambda x, arg: x.warning(f'{x.current_buffer.cursor_lin_col = }'),
    }

class ChoiceList(BaseBehaviour):
    stand_alone_commands = {
    # page scrolling 
        k.page_up   : DO_page_up,
        k.page_down : DO_page_down,
    }
    
    full_commands = {
        '/'     : DO_find,
        'n'     : DO_normal_n,
    }

    motion_commands = {
        k.up    : 'k',
        'k' : lambda ed, cmd: ed.current_buffer.go_up(),
        k.down  : 'j',
        'j' : lambda ed, cmd: ed.current_buffer.go_down(),
    }

class ReadOnlyText(BaseBehaviour):
    stand_alone_commands = {
    # page scrolling 
        k.page_up   : DO_page_up,
        k.page_down : DO_page_down,}
    
    full_commands = {
        '/'     : DO_find,
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
    # other
        ' '     : 'l',
        '\r'    : 'j', })

GO = lambda where: lambda ed, cmd: ed.current_buffer.move_cursor(where)

class WritableText(ReadOnlyText):
    """The behaviour of a «standard» text file buffer."""

    stand_alone_commands = {
        'p' : DO_paste,
    # goto insert_mode
        'O'   : do( GO('0'), r"x.current_buffer.insert('\n')", GO('k'), mode='insert'),
        'o'   : do( GO('$'), r"x.current_buffer.insert('\n')", mode='insert'),
        'i'   : do(mode='insert'),
        'I'   : do( GO('0'), mode='insert'),
        'a'   : do( GO('l'), mode='insert'),
        'A'   : do( GO('$'), mode='insert'),
        k.insert    : do(mode='insert'),
        'i'   : do(mode='insert'),
# misc
        k.C_R   : lambda ed, cmd: ed.current_buffer.redo(),
        'u'     : lambda ed, cmd: ed.current_buffer.undo(),

# edition
        k.suppr : 'x',
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

