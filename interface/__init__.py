"""
    ***********************************
    ****    Modes And Interface    ****
    ***********************************
    
In Vy, Modes are responsible for parsing user input, and trigerring
appropriate actions.

The 'vy.interface' module contains the implementation of the basic
modes.  Custom modes may be added and reloaded at any time.  All you
need is an action that returns a string, that correspond to one of the
files inside vy/interface/ directory.

Modes can be divided in two categories, some parsing user key-strokes at
character level (like 'normal' and 'visual' modes), other operating on a
line, (like 'command' and 'ex' mode).

For reading single characters, modes can use the Editor.read_stdin()
method.  If the main mode is currently delegating its job to a sub-mode,
the sub-mode is expected to use the Editor.visit_stdin() method.

If the sub-mode succeeds in handling the key that was pressed, it makes a
call to Editor.read_stdin() to discard the character from the input
queue, otherwise it just return its parent mode name as a string.

The 'vy.interface.helpers' module contains an implementation of a
readline() function with editing capacities and per-mode history, see 
':help vy.interface.helpers' to learn more about it.
"""
from importlib import import_module, reload
from sys import modules

class Interface():
    __slots__ = ('inst', 'mode_dict')

    def __init__(self, inst):
        self.inst = inst
        self.mode_dict = {}
    
    def __call__(self, mode_chain):
        if ':' not in mode_chain:
            return self.find_mode_and_execute_it(mode_chain)
        
        chain = mode_chain.split(':')
        for mode in chain[:-1]:
            self.find_mode_and_execute_it(mode)
        return self.find_mode_and_execute_it(chain[-1])
        
    
    def find_mode_and_execute_it(self, name):
        loop = self.mode_dict.get(name, None)
        if loop is not None:
            return loop(self.inst)
            
        mod_name = f'vy.interface.{name}'
        if mod_name in modules:
            reload(modules[mod_name])
        
        module = import_module(mod_name, __package__)
        if hasattr(module, 'init'):
            module.init(self.inst)
        loop = module.loop
        self.mode_dict[name] = loop
        
