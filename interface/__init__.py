from importlib import import_module

class Interface():
    __slots__ = ('last', 'inst', 'mode_dict')

    def __init__(self, inst):
        self.last = 'normal'
        self.inst = inst
        self.mode_dict = {}
    
    def __call__(self, name=None):
        if name is None: 
            return self.mode_dict[self.last].loop(self.inst)
        try:
            return self.mode_dict[name].loop(self.inst)
        except KeyError:
            try:
                self.mode_dict[name] = import_module(f'.{name}', 'Vy.interface')
                return self.mode_dict[name].loop(self.inst)
            except ImportError:
                self.inst.warning(f"Vy can't find the definition of {name} mode.")
        finally:
            self.last = name
