def do(*arg_list, mode=None):
    doc = 'This command is does the following actions:\n'
    for arg_item in arg_list:
        if callable(arg_item) and arg_item.__doc__:
            doc += arg_item.__doc__ + '\n'
        elif isinstance(arg_item, str):
            doc += f"lambda function where x is the editor and arg the following of the line:\n lambda x, arg: {arg_item}" 
    def func(ed, cmd):
        for arg_item in arg_list:
            if callable(arg_item):
                arg_item(ed, cmd)
            elif isinstance(arg_item, str):
                eval(f"lambda x,arg: {arg_item}")(ed, cmd) 
        return mode
    func.__doc__ = doc
    return func

def resolver(mapping, key=None, default=None):
    tried = set()
    while True:
        try:
            rv = mapping[key]
        except KeyError:
            return default
        if rv in tried:
            raise RecursionError
        if callable(rv):
            return rv
        else:
            tried.add(rv)
            key = rv

def one_inside_dict_starts_with(dictio, pattern):
    maybe = False
    for key in dictio:
        try:
            if key.startswith(pattern):
                if key != pattern:
                    return True
                else:
                    maybe = True
        except AttributeError:
            pass
    return maybe
