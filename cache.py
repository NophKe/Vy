from .filetypes import ReadOnlyTextFile, TextFile, Folder, HugeFile
from pathlib import Path

# helper function
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
    """Simple wrapper around a dict that lets you index a buffer by its
    internal id, or any relative or absolute version of its path.
    """
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
            """This is the main api of this class.
            It takes an only argument that can be a string, a path object,
            an int, or None. 
            If the argument is a string or a path object, it will be resolved 
            to an absolute path, and if this path has allready been cached,
            the correponding buffer will be returned. If not, a new buffer
            will be created from reading the path content or from scratch.
            Pas it an int for buffers unrelated to file system.
            Pass it None to create a new unnamed buffer.
            """
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
                self._dic[name] = self._open_path(name, **kwargs)
                rv = self._dic[name]
                rv.cache_id = name
                return rv

    def _open_path(self, location):
        if (location in self):
            return self.cache.get(location)
        if (location is None):
            return TextFile(location)

        if isinstance(location, (Path, str)):
            location = Path(location).resolve()
            if location.is_dir():
                return Folder(location)
            
            if location.exists() and location.is_file():
                if location.lstat().st_size > 1_000_000_000:
                    return HugeFile(location)

                try:
                    open(location, 'r')
                except PermissionError as exc:
                    return self.current_buffer

                try:
                    open(location, 'a')
                except PermissionError as exc:
                    return ReadOnlyTextFile(location)
                
                return TextFile(location)

            if not location.exists():
                try:
                    open(location, 'w')
                except PermissionError as exc:
                    # TODO # replace that input func by call to ed.warning
                    input('you do not seem to have the rights to write in here.')
                    return self.current_buffer
                return TextFile(location)
