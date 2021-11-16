"""
This module contains the default global configuration.
The variables defined here will be overriden by command line invocation.
"""
from pathlib import Path
USER_DIR = Path('~/.vy/').expanduser()
del Path

DONT_USE_PYGMENTS_LIB = False
DONT_USE_USER_CONFIG = False
