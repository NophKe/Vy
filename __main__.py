#!/usr/bin/python3 -O -u -m

#######   BASIC INITIALISATION #############################

if __name__ != '__main__':
    raise ImportError(
    'This file is the main entry point for the Vym Editor and '
    'is not supposed to be imported, but executed by: python -m Vy')
try:
    from . import global_config
except ImportError:
    raise ImportError(
    'This file is the main entry point for the Vym Editor and '
    'is not supposed to be executed outside the Vy package. Use: python -m Vy')

########   COMMAND LINE PARSING #############################

from argparse import ArgumentParser 
parser = ArgumentParser(prog='Vy',
                        description='LEGACY-FREE VI-LIKE EDITOR',
                        )
parser.add_argument('--debug',
                    action="store_true",
                    default=False,
                    help='Make ^C dump infos and enter the debugger.')
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

########    UPDATE CONGIGURATION    ##################################

global_config.DONT_USE_PYGMENTS_LIB = cmdline.no_pygments
global_config.DONT_USE_USER_CONFIG  = cmdline.no_user_config

if not global_config.USER_DIR.exists() and not global_config.DONT_USE_USER_CONFIG:
    global_config.USER_DIR.mkdir()

########    SIGNAL HANDLING    #######################################

from signal import signal, SIGWINCH, SIGINT

signal(SIGWINCH, lambda a, b: Editor.show_screen(False))


########    DEBUG MODE     ###########################################

if cmdline.debug:
    """ Be Aware that debug mode is buggy !!! """
    import sys
    from pprint import pp
    import faulthandler

    def dump_infos(a, b):
        Editor.screen.original_screen()
        sys.stdout.flush()
        items = [ Editor.current_buffer, 
                Editor.screen, Editor.cache, Editor.registr ]
        for item in items:
            pp(item.__dict__)
            input(repr(item) + 'ok?  ')
        print(repr(a) + 'ok?  ')
        print(repr(b) + 'ok?  ')
        faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
        sys.stdin.readline()
    signal(SIGINT, dump_infos)


########    START THE EDITOR #########################################

from vy.editor import _Editor as Editor
Editor = Editor(*cmdline.files, command_line=cmdline)

import sys
sys.exit(Editor(mode=cmdline.mode))
