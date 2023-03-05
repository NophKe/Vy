"""
This module contains the default global configuration.
The variables defined here will be overriden by command line invocation.
"""
from pathlib import Path as _path
USER_DIR = _path('~/.vy/').expanduser()
def _source_config():
    global USER_DIR
    user_dir = USER_DIR
    if not user_dir.exists():
        user_dir.mkdir()
    start_script = user_dir / "config"
    if start_script.exists():
        for line in start_script.read_text().splitlines():
            # Should this be secured ? It's a personal config file !
            exec(line,globals(),globals())

def _source_rcfile(editor):
    rcfile = USER_DIR / "rcfile.py"
    if rcfile.exists():
        exec(rcfile.read_text(),{'vy':editor},{})
    

DEBUG = False
DONT_USE_PYGMENTS_LIB = False
DONT_USE_JEDI_LIB = False
DONT_USE_USER_CONFIG = False
