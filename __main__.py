if __name__ != '__main__':
    raise ImportError('This file is the main entry point for the Vym Editor and '
                      'is not supposed to be imported, but executed by: python -m Vy')
try:
    from . import global_config
except ImportError:
    raise ImportError('This file is the main entry point for the Vym Editor and '
                      'is not supposed to be executed outside the Vy package. Use: python -m Vy')
from signal import signal, SIGWINCH, SIGINT

signal(SIGWINCH, lambda a, b: Editor.screen.show(False))
signal(SIGINT, lambda a, b: None)

from argparse import ArgumentParser 
parser = ArgumentParser(prog='Vy',
                        description='Legacy-free Vi-like editor',
                        )
parser.add_argument('--__server__',
                    default='editor',
                    choices=('editor', 'screen'),
                    help='Used by Vy internals ( WIP NOT DOCUMENTED!)')
parser.add_argument('--mode',
                    default='normal',
                    choices=('normal', 'command', 'python', 'insert'),
                    help='Mode in which the editor lauches.')
parser.add_argument('--no-user-config', 
                    action="store_true",
                    default=False,
                    help='Do not read user config folder.')
parser.add_argument('--no-pygments',
                    action="store_true",
                    default=False,
                    help='Do not use Pygments library for syntax hilighting even if available.')
parser.add_argument("files",
                    help="List of files to Open.", 
                    nargs='*', 
                    default=None)

cmdline = parser.parse_args()

global_config.DONT_USE_PYGMENTS_LIB = cmdline.no_pygments
global_config.DONT_USE_USER_CONFIG  = cmdline.no_user_config

if (not global_config.USER_DIR.exists() and not global_config.DONT_USE_USER_CONFIG):
    global_config.USER_DIR.mkdir()

from vy.editor import Editor
Editor = Editor(*cmdline.files, command_line=cmdline)

import sys
sys.exit(Editor(mode=cmdline.mode))
