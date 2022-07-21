from importlib import import_module
#from time import sleep

class Interface():
    __slots__ = ('inst', 'mode_dict')

    def __init__(self, inst): #, mode='normal'):
        #self.last = mode
        self.inst = inst
        self.mode_dict = {}
    
    def __call__(self, name):
        loop = None
        #if name is None: 
            #try:
                #loop = self.mode_dict[self.last].loop
            #except KeyError:
                #pass

        #if loop is None:
        try:
            loop = self.mode_dict[name].loop
        except KeyError:
            loop = None

        if loop is None:
            try:
                module = import_module(f'vy.interface.{name}', __package__)
                if hasattr(module, 'init'):
                    module.init(self.inst)
                loop = module.loop
            except ImportError:
                self.inst.warning(f"Vy can't find the definition of {name} mode.")
                return "normal"
        #self.last = name if name else self.last

        #sleep(0)
        return loop(self.inst)
