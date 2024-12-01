from vy.global_config import USER_DIR, DONT_USE_USER_CONFIG
import atexit as _atexit

class _Register:
    __slots__ = ("persistance", "dico")
    valid_registers  = ( 'abcdefghijklmnopqrstuvwxyz'
                         'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                         '>+-*/.:%#"=!0123456789')
    def __init__(self):
        self.dico = dict()
        if not DONT_USE_USER_CONFIG:
            self.persistance = USER_DIR / 'registers'
            try:
                content = self.persistance.read_text().splitlines()
            except FileNotFoundError:
                content = ["''"] * len(self.valid_registers)
                self.persistance.touch()
                self.persistance.write_text('\n'.join(content))
            
            for register, value in zip(self.valid_registers, content):
                if value := eval(value):
                    self.dico[register] = value

            _atexit.register(self.save)
        
    def save(self):
        self.persistance.write_text('\n'.join(repr(self.dico.get(reg, '')) for reg in self.valid_registers))

    def __str__(self):
        rv = str()
        for k,v in self.dico.items():
            rv += k +'\t:\t' + v.replace('\n', '\\n') + '\n'
        return rv

    def __getitem__(self, key):
        if isinstance(key, int):
            key = str(key)
        assert isinstance(key, str)
        assert key in self.valid_registers
        if key == '+':
            try:
                self['"'] = (rv := get_os_clipboard())
                return rv
            except _NotWorking:
                return self.dico['"']
            
        try:
            return self.dico[key]
        except KeyError:
            return ''

    def __setitem__(self, key, value):
        if isinstance(key, int):
            key = str(key)
        assert isinstance(key, str)
        assert key in self.valid_registers

        if key == '_':
            return
        elif key == '+':
            set_os_clipboard(value)
            self['"'] = value
        
        elif key in ':.>':
            self.dico[key] = value

        elif key == '"':
            for k in range(9,0,-1):
                self[str(k)] = self[str(k-1)]
            self["0"] = self['"']
            self.dico['"'] = value
        
        elif key.isupper():
            key = key.lower()
            if key in self.dico:
                self.dico[key] += value
            else:
                self.dico[key] = value
            self['"'] = self.dico[key]
            
        elif key.islower():
            self.dico[key] = value
            self['"'] = self.dico[key]
        
        elif key.isnumeric() or key == '/':
            self.dico[key] = value
        
        elif key == '=':
            self.dico[key] = eval(value)
        
        elif key == '!':
            self.dico[key] = exec(value)

        else:
            raise RuntimeError

class _NotWorking(RuntimeError):
    pass
    
def _not_working(*args):
    raise _NotWorking

get_os_clipboard = set_os_clipboard = _not_working

try:
    import copykitten
    get_os_clipboard = copykitten.paste
    set_os_clipboard = copykitten.copy
except ImportError:
    pass

try:
    import pyperclip
    get_os_clipboard = pyperclip.paste
    set_os_clipboard = pyperclip.copy
    _NotWorking = pyperclip.PyperclipException
except ImportError:
    pass

try:
    set_os_clipboard(get_os_clipboard())
except _NotWorking:
    try:
        import subprocess
        def get_os_clipboard():
            return subprocess.getoutput('termux-clipboard-get')
            
        def set_os_clipboard(new_value):
            worker = subprocess.Popen('termux-clipboard-set', 
                                        text=True,
                                        stdin=subprocess.PIPE)
            out, err = worker.communicate(new_value)
            
        set_os_clipboard(get_os_clipboard())
    except:
        def get_os_clipboard():
            raise _NotWorking
        def set_os_clipboard(new_value):
            pass
