bad_string = "H̹̙̦̮͉̩̗̗ͧ̇̏̊̾Eͨ͆͒̆ͮ̃͏̷̮̣̫̤̣Cͯ̂͐͏̨̛͔̦̟͈̻O̜͎͍͙͚̬̝̣̽ͮ͐͗̀ͤ̍̀͢M̴̡̲̭͍͇̼̟̯̦̉̒͠Ḛ̛̙̞̪̗ͥͤͩ̾͑̔͐ͅṮ̴̷̷̗̼͍̿̿̓̽͐H̙̙̔̄͜"
#print(f'{len(bad_string) =}')


# This class should one day replace the command class
class CMD:
    def __new__(cls, *args, **kwargs):
        cls.seen = set()
        super.__new__(cls, *args, **kwargs)
    def __init_subclass__(cls, /, alias_dict, **kwargs):
        self.alias_dict = alias_dict
        super().__init_subclass__(cls, **kwargs)
    def __init__(self, header, mode_prefix):
        self.header = self.v_header % (v_alias[0] ,
                                    ' '.join(_escape(item) for item in v_alias).ljust(60))
    def update_func(self, alias, func):
        for item in alias.split(' '):
            self.alias_dict[alias] = func
        header = ''
        if func.__doc__:
            func.__doc__ = self.header + '\n' + func.__doc__ + '\n'
    def __call__(self, alias):
        return lambda func : self.update_func(alias, func)
 
