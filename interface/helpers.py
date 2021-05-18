def do(*arg_list, mode=None):
    def func(ed, cmd):
        for arg_item in arg_list:
            if callable(arg_item): 
                arg_item(ed, cmd)
            elif isinstance(arg_item, str):
                eval(f"lambda x,arg: {arg_item}")(ed, cmd) 
        return mode
    return func

def resolver(mapping, key=None, default=None):
    assert key
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
