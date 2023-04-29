"""
    *******************************
    ****    The Help System    ****
    *******************************

Vy is shipped with its internal help system.  The vy.help module
contains the functions used to generate the documentation documents.

The help about the vy.help module documents this process.
"""
from importlib import import_module
from inspect import signature

def resolver(help_file):
    if callable(help_file):
        return help_file.__doc__ or ''
    return section_builder(help_file)

def section_builder(module):        
#    mod_name = f'vy.{module_name}'
#    module = import_module(mod_name, __package__)
    sub_sections = [module.__doc__] if module.__doc__ else []
    for k, v in module.__dict__.items():
        if hasattr(v, '__module__') and 'vy' not in v.__module__:
            continue
        if not k.startswith('_') and callable(v):
            try:
                call_convention = str(signature(v))
            except ValueError:
                call_convention = ''

            if hasattr(v, '__doc__') and v.__doc__:
                sub_sections.append(f'''
{str(k).upper()} 
    {'-'*68}
    {f'{v.__module__}.{k}{call_convention}':68}{v.__doc__}''' ) 

        elif (isinstance(v, str) and k.startswith('doc')):
                sub_sections.append(v)
    return '\n'.join(sub_sections)
