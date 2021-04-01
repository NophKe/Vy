from . import (insert_mode, command_mode, normal_mode, python_mode)

class Interface():
    __slots__ = ('last', 'inst', 'mode_dict')

    def __init__(self, inst):
        self.last = None
        self.inst = inst
        self.mode_dict = {}
        self.add_mode('normal', normal_mode)   
        self.add_mode('command', command_mode)   
        self.add_mode('insert', insert_mode)   
        self.add_mode('python', python_mode)   
    
    def __call__(self, name):
        if self.inst._running_flag:
            print('\tyou cannot interract with the editor stacking call to:')
            print('\tEditor()')
            print('\tEditor.interface()')
            print('\tand such...')
            raise
        assert (name in self.mode_dict) or self.last
        if name: 
            self.last = name
            return self.mode_dict[name].loop(self.inst)
        else:
            return self.mode_dict[self.last].loop(self.inst)

    def add_mode(self, name, mode):
        assert isinstance(name, str)
        assert hasattr(mode, 'loop')
        assert callable(mode.loop)

        if name not in self.mode_dict:
            self.mode_dict[name] = mode
