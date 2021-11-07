from vy.keys import _escape
class command:
    def __init__(self, c_header, n_header, v_header, i_header, category):
        self.c_header = c_header
        self.n_header = n_header
        self.v_header = v_header
        self.i_header = i_header
        self.category = category

    def update_func(self, alias, func):
        c_alias: list = list()
        n_alias: list = list()
        v_alias: list = list()
        i_alias: list = list()

        for item in alias.split(" "):
            if not item                 : continue
            elif len(item) == 1         : n_alias.append(item)
            elif item.startswith('v_')  : v_alias.append(item.removeprefix('v_'))
            elif item.startswith('i_')  : i_alias.append(item.removeprefix('i_'))
            elif item.startswith(':')   : c_alias.append(item.removeprefix(':'))
            else                        : n_alias.append(item)

        header = ''
        if c_alias:
            header += self.c_header % (c_alias[0] ,
                                    ' '.join(_escape(item) for item in c_alias).ljust(60))
        if n_alias:
            header += self.n_header % (n_alias[0] ,
                                    ' '.join(_escape(item) for item in n_alias).ljust(60))
        if v_alias:
            header += self.v_header % (v_alias[0] ,
                                    ' '.join(_escape(item) for item in v_alias).ljust(60))
        if i_alias:
            header += self.i_header % (i_alias[0] ,
                                    ' '.join(_escape(item) for item in i_alias).ljust(60))

        func.stand_alone = func.with_args  = func.full = func.atomic = False
        setattr(func, self.category, True)

        func.n_alias = n_alias if n_alias else None
        func.c_alias = c_alias if c_alias else None
        func.v_alias = v_alias if v_alias else None
        func.i_alias = i_alias if i_alias else None

        func.__doc__ = header + func.__doc__ if func.__doc__ else ''
        return func

    def __call__(self, alias):
        return lambda func : self.update_func(alias, func)

v_sa_header = """
    This command is part of visual mode «stand-alone commands» commands.

    [SYNTAX]    needs definition %s 
    aliases: %s
    -------------------------------------------------------------------- """
i_sa_header = """
    This command is part of insert mode «stand-alone commands» commands.

    [SYNTAX]    needs definition %s 
    aliases: %s
    -------------------------------------------------------------------- """
c_sa_header = """
    This command is part of command mode «stand-alone commands» commands.

    [SYNTAX]      :[%s] {register}
    aliases: %s
    -------------------------------------------------------------------- """
n_sa_header = """
    This command is part of normal mode «stand-alone commands» commands.

    [SYNTAX]      ["{register}] [{count}] %s
    aliases: %s
    -------------------------------------------------------------------- """
sa_commands = command(c_sa_header, n_sa_header, v_sa_header, i_sa_header, "stand_alone")


v_full_header = """
    This command is part of visual mode «full» commands.

    [SYNTAX]    needs definition %s 
    aliases: %s
    -------------------------------------------------------------------- """
i_full_header = """
    This command is part of insert mode «full» commands.

    [SYNTAX]    needs definition %s
    aliases: %s
    -------------------------------------------------------------------- """
c_full_header = """
    This command is part of command mode «full» commands.

    [SYNTAX]      :%s {register}
    aliases: %s
    -------------------------------------------------------------------- """
n_full_header = """
    This command is part of normal mode «full» commands.

    [SYNTAX]      ["{register}] [{count}] %s [{count}] {motion}
    aliases: %s
    -------------------------------------------------------------------- """
full_commands = command(c_full_header, n_sa_header, v_sa_header, i_sa_header, "full")


v_atomic_header = """
    This command is part of visual mode «atomic» commands.

    [SYNTAX]      %s
    aliases: %s
    -------------------------------------------------------------------- """
i_atomic_header = """
    This command is part of insert mode «atomic» commands.

    [SYNTAX]      %s
    aliases: %s
    -------------------------------------------------------------------- """
c_atomic_header = """
    This command is part of command mode «atomic» commands.

    [SYNTAX]      :%s
    aliases: %s
    -------------------------------------------------------------------- """
n_atomic_header = """
    This command is part of normal mode «atomic» commands.

    [SYNTAX]      %s
    aliases: %s
    -------------------------------------------------------------------- """
atomic_commands = command(c_atomic_header, n_sa_header, v_sa_header, i_sa_header, "atomic")


v_with_args_header = """
    This command is part of visual mode «with args» commands.

    [SYNTAX]      needs definition %s
    aliases: %s
    -------------------------------------------------------------------- """
i_with_args_header = """
    This command is part of insert mode «with args» commands.

    [SYNTAX]      needs definition %s
    aliases: %s
    -------------------------------------------------------------------- """
c_with_args_header = """
    This command is part of command mode «with args» commands.

    [SYNTAX]      :%s {argument}
    aliases: %s
    -------------------------------------------------------------------- """
n_with_args_header = """
    This command is part of normal mode «with args» commands.

    [SYNTAX]      needs definition %s
    aliases: %s
    -------------------------------------------------------------------- """
with_args_commands = command(c_with_args_header, n_with_args_header, v_with_args_header, i_with_args_header, "with_args")


v_with_args_header = """
    This command is part of visual mode «with args» commands.

    [SYNTAX]      needs definition %s
    aliases: %s
    -------------------------------------------------------------------- """
i_with_args_header = """
    This command is part of insert mode «with args» commands.

    [SYNTAX]      needs definition %s
    aliases: %s
    -------------------------------------------------------------------- """
c_with_args_header = """
    This command is part of command mode «with args» commands.

    [SYNTAX]      :%s {argument}
    aliases: %s
    -------------------------------------------------------------------- """
n_with_args_header = """
    This command is part of normal mode «with args» commands.

    [SYNTAX]      needs definition %s
    aliases: %s
    -------------------------------------------------------------------- """
with_args_commands = command(c_with_args_header, n_with_args_header, v_with_args_header, i_with_args_header, "with_args")
