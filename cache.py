from pathlib import Path
from .filetypes import TextFile

def _make_key(key):
    if isinstance(key, int):
        return key
    elif isinstance(key, str):
       return str(Path(key).resolve()) 
    elif isinstance(key, Path):
        return str(key.resolve())
    else:
        raise ValueError

class Cache():
    _dic = dict()
    _counter = 1

    def pop(self, key):
        return self._dic.pop(_make_key(key))

    def __repr__(self):
        rv = str()
        for buff in self._dic.values():
            rv += f'cache_id: {buff.cache_id} : {repr(buff)}\n'
        return rv

    def __iter__(self):
        for value in self._dic.values():
            yield value
    
    def __contains__(self, key):
        if key in self._dic:
            return True
        elif _make_key(key) in self._dic:
            return True
        else:
            return False

    def get(self, item):
            if item is None:
                return self._add(item)
            elif item in self._dic.values():
                return item
            elif _make_key(item) in self:
                return self._dic[_make_key(item)]
            else:
                return self._add(item)

    def _add(self, name=None, **kwargs):
        if name is None:
            self._dic[int(self._counter)] = TextFile(**kwargs)
            rv = self._dic[self._counter]
            rv.cache_id = self._counter
            self._counter +=1
            return rv
        else:
            name = _make_key(name)    
            if name in self:
                raise ValueError('Allready in cache')
            else:
                self._dic[name] = TextFile(name, **kwargs)
                rv = self._dic[name]
                rv.cache_id = name
                return rv
