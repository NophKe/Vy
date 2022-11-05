from importlib import import_module

class Interface():
    __slots__ = ('inst', 'mode_dict')

    def __init__(self, inst): #, mode='normal'):
        self.inst = inst
        self.mode_dict = {}
    
    def __call__(self, name):
        loop = self.mode_dict.get(name, None)

        if loop is None:
            try:
                module = import_module(f'vy.interface.{name}', __package__)
                if hasattr(module, 'init'):
                    module.init(self.inst)
                loop = module.loop
                self.mode_dict[name] = loop
            except ImportError:
                self.inst.warning(f"Vy can't find the definition of {name} mode."
                                    "or syntaxError while reading mode defintion")
                return "normal"

        return loop(self.inst)
