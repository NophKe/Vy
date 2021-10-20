def command(c_header, n_header, v_header, i_header, category):
    def decorator(alias):
        def wrapper(func):
            c_alias = list()
            n_alias = list()
            v_alias = list()
            i_alias = list()
            if not hasattr(func, 'category'):
                func.category = list()

            for item in alias.split(" "):
                if not item: continue
                elif item.startswith('v_'): v_alias.append(item.removeprefix('v_'))
                elif item.startswith('i_'): i_alias.append(item.removeprefix('i_'))
                elif item.startswith(':'): c_alias.append(item.removeprefix(':'))
                else: n_alias.append(item)

            header = ''
            if c_alias:
                header += c_header % (c_alias[0] , ' '.join(c_alias).ljust(60))
                func.category.append(f'command_{category}')
            if n_alias:
                header += n_header % (n_alias[0] , ' '.join(n_alias).ljust(60))
                func.category.append(f'normal_{category}')
            if v_alias:
                header += v_header % (v_alias[0] , ' '.join(n_alias).ljust(60))
                func.category.append(f'visual_{category}')
            if i_alias:
                header += i_header % (i_alias[0] , ' '.join(n_alias).ljust(60))
                func.category.append(f'insert_{category}')

            func.n_alias = n_alias
            func.c_alias = c_alias
            func.v_alias = v_alias
            func.i_alias = i_alias

            func.__doc__ = header + func.__doc__ if func.__doc__ else ''
            return func
        return wrapper
    return decorator 

v_sa_header = """
    This command is part of visual mode «stand-alone commands» commands.

    [SYNTAX]    needs definition %s 
    aliases: %s
    --------------------------------------------------------------------
"""

i_sa_header = """
    This command is part of insert mode «stand-alone commands» commands.

    [SYNTAX]    needs definition %s 
    aliases: %s
    --------------------------------------------------------------------
    """
c_sa_header = """
    This command is part of command mode «stand-alone commands» commands.

    [SYNTAX]      :[%s] {register}
    aliases: %s
    --------------------------------------------------------------------
"""

n_sa_header = """
    This command is part of normal mode «stand-alone commands» commands.

    [SYNTAX]      ["{register}] [{count}] %s
    aliases: %s
    --------------------------------------------------------------------
"""

sa_commands = command(c_sa_header, n_sa_header, v_sa_header, i_sa_header, "stand_alone")

##############################################################################

v_full_header = """
    This command is part of visual mode «full» commands.

    [SYNTAX]    needs definition %s 
    aliases: %s
    --------------------------------------------------------------------
"""

i_full_header = """
    This command is part of insert mode «full» commands.

    [SYNTAX]    needs definition %s
    aliases: %s
    --------------------------------------------------------------------
    """

c_full_header = """
    This command is part of command mode «full» commands.

    [SYNTAX]      :%s {register}
    aliases: %s
    --------------------------------------------------------------------
"""

n_full_header = """
    This command is part of normal mode «full» commands.

    [SYNTAX]      ["{register}] [{count}] %s [{count}] {motion}
    aliases: %s
    --------------------------------------------------------------------
"""

full_commands = command(c_full_header, n_sa_header, v_sa_header, i_sa_header, "full")

##############################################################################

v_atomic_header = """
    This command is part of visual mode «atomic» commands.

    [SYNTAX]      %s
    aliases: %s
    --------------------------------------------------------------------
"""

i_atomic_header = """
    This command is part of insert mode «atomic» commands.

    [SYNTAX]      %s
    aliases: %s
    --------------------------------------------------------------------
    """
c_atomic_header = """
    This command is part of command mode «atomic» commands.

    [SYNTAX]      :%s
    aliases: %s
    --------------------------------------------------------------------
"""

n_atomic_header = """
    This command is part of normal mode «atomic» commands.

    [SYNTAX]      %s
    aliases: %s
    --------------------------------------------------------------------
"""
atomic_commands = command(c_atomic_header, n_sa_header, v_sa_header, i_sa_header, "atomic")

##############################################################################

v_with_args_header = """
    This command is part of visual mode «with args» commands.

    [SYNTAX]      needs definition %s
    aliases: %s
    --------------------------------------------------------------------
"""

i_with_args_header = """
    This command is part of insert mode «with args» commands.

    [SYNTAX]      needs definition %s
    aliases: %s
    --------------------------------------------------------------------
    """
c_with_args_header = """
    This command is part of command mode «with args» commands.

    [SYNTAX]      :%s {argument}
    aliases: %s
    --------------------------------------------------------------------
"""

n_with_args_header = """
    This command is part of normal mode «with args» commands.

    [SYNTAX]      needs definition %s
    aliases: %s
    --------------------------------------------------------------------
"""
with_args_commands = command(c_with_args_header, n_with_args_header, v_with_args_header, i_with_args_header, "with_args")

##############################################################################
