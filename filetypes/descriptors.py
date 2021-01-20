from pathlib import Path

class VyPath:
    def __get__(self, inst, objtype=None):
        return inst._path
    def __set__(self, inst, value):
        assert isinstance(value, (str, Path, type(None)))
        if value is None:
            inst._path = None
        elif isinstance(value, str):
            inst._path = Path(value).resolve()
        elif isinstance(value, Path):
            inst._path = value.resolve()

class VyString:
    def __get__(self, inst, objtype=None):
        return inst._string
    def __set__(self, inst, value):
        assert isinstance(value, str)
        if not inst._no_undoing:
            inst.undo_list.append((inst._string, inst.cursor))
        inst._string = value
        if inst.redo_list:
            inst.redo_list = list()
