from vy.keys import _escape
from vy.actions import action_dicts

class _command:
    def update_func(self, alias, func):
        c_alias = []
        n_alias = []
        v_alias = []
        i_alias = []

        for item in alias.split(" "):
            if not item                 : continue
            elif len(item) == 1         : n_alias.append(item) 
            # if item == ':':           : n_alias.append(item)
            elif item.startswith('v_')  : v_alias.append(item.removeprefix('v_'))
            elif item.startswith('i_')  : i_alias.append(item.removeprefix('i_'))
            elif item.startswith(':')   : c_alias.append(item.removeprefix(':'))
            else                        : n_alias.append(item)

        separator = '\n    ' + '-' * 68 #+ '\n'
        header = separator
        if c_alias:
            header += self.c_header % (_escape(c_alias[0]) ,
                                    ' '.join(_escape(item) for item in c_alias).ljust(60))
            header += separator
        if n_alias:
            header += self.n_header % (_escape(n_alias[0]) ,
                                    ' '.join(_escape(item) for item in n_alias).ljust(60))
            header += separator
        if v_alias:
            header += self.v_header % (_escape(v_alias[0]) ,
                                    ' '.join(_escape(item) for item in v_alias).ljust(60))
            header += separator
        if i_alias:
            header += self.i_header % (_escape(i_alias[0]) ,
                                    ' '.join(_escape(item) for item in i_alias).ljust(60))
            header += separator
        if any((i_alias, n_alias, c_alias, v_alias,)):
            header += '\n'

        func.motion = func.stand_alone = func.with_args  = func.full = func.atomic = False
        setattr(func, self.category, True)

        func.n_alias = n_alias if n_alias else None
        func.c_alias = c_alias if c_alias else None
        func.v_alias = v_alias if v_alias else None
        func.i_alias = i_alias if i_alias else None

        func.__doc__ = header + (func.__doc__ or '')
        return func

    def __call__(self, alias):
        return lambda func : self.update_func(alias, func)

class sa_commands(_command):
    v_header = """
    This command is part of visual mode «stand-alone commands» commands.

    [SYNTAX]    MAY BE LATER DEFINED %s 
    aliases: %s"""
    
    i_header = """
    This command is part of insert mode «stand-alone commands» commands.

    [SYNTAX]    MAY BE LATER DEFINED %s 
    aliases: %s"""
    
    c_header = """
    This command is part of command mode «stand-alone commands» commands.

    [SYNTAX]      :%s {register}
    aliases: %s"""
    
    n_header = """
    This command is part of normal mode «stand-alone commands» commands.

    [SYNTAX]      ["{register}] [{count}] %s
    aliases: %s"""
    category = "stand_alone"
sa_commands = sa_commands()

class full_commands(_command):
    v_header = """
    This command is part of visual mode «full» commands.

    [SYNTAX]      ["{register}] [{count}] {motion} %s 
    aliases: %s"""
    
    i_header = """
    This command is part of insert mode «full» commands.

    [SYNTAX]    MAY BE LATER DEFINED %s
    aliases: %s"""
    
    c_header = """
    This command is part of command mode «full» commands.

    [SYNTAX]      :%s {register}
    aliases: %s"""
    
    n_header = """
    This command is part of normal mode «full» commands.

    [SYNTAX]      ["{register}] [{count}] %s [{count}] {motion}
    aliases: %s"""
    category = "full"
full_commands = full_commands()
    
class atomic_commands(_command):
    v_header = """
    This command is part of visual mode «atomic» commands.

    [SYNTAX]      %s
    aliases: %s"""
    
    i_header = """
    This command is part of insert mode «atomic» commands.

    [SYNTAX]      %s
    aliases: %s"""
    
    c_header = """
    This command is part of command mode «atomic» commands.

    [SYNTAX]      :%s
    aliases: %s"""
    
    n_header = """
    This command is part of normal mode «atomic» commands.

    [SYNTAX]      %s
    aliases: %s"""
    category = "atomic"
atomic_commands = atomic_commands()

class with_args_commands(_command):
    v_header = """
    This command is part of visual mode «with args» commands.

    [SYNTAX]      MAY BE LATER DEFINED %s
    aliases: %s"""
    
    i_header = """
    This command is part of insert mode «with args» commands.

    [SYNTAX]      MAY BE LATER DEFINED %s
    aliases: %s"""
    
    c_header = """
    This command is part of command mode «with args» commands.

    [SYNTAX]      :%s {argument}
    aliases: %s"""
    
    n_header = """
    This command is part of normal mode «with args» commands.

    [SYNTAX]      MAY BE LATER DEFINED %s
    aliases: %s"""
    category = "with_args"
with_args_commands = with_args_commands()
