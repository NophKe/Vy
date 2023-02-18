#!/usr/bin/python3 -m
"""
This file is the main entry point for the Vy Editor and is not supposed 
to be executed outside the Vy package. This module is in charge of basic
initialization. To see all available option on command line, use:
 python -m vy --help
"""

#######   BASIC INITIALISATION #############################

if __name__ != '__main__':
    raise ImportError(
    'This file is the main entry point for the Vy Editor and '
    'is not supposed to be imported, but executed by: python -m vy')
try:
    from . import global_config
except ImportError:
    raise ImportError(
    'This file is the main entry point for the Vy Editor and '
    'is not supposed to be executed outside the Vy package. Use: python -m Vy')

########   COMMAND LINE PARSING #############################

from argparse import ArgumentParser 

parser = ArgumentParser(prog='Vy',
                        description='LEGACY-FREE VI-LIKE EDITOR',)

parser.add_argument('--profile', default=False,
            action="store_true",
            help='Screen shows selected infos and enter the debugger.')

parser.add_argument('--debug', default=False,
            action="store_true",
            help='Screen shows selected infos and enter the debugger.')

parser.add_argument('--mode', default='normal',
            choices=('normal', 'command', 'python', 'insert'),
            help='Mode in which the editor lauches.')

parser.add_argument('--no-user-config', default=False,
            action="store_true",
            help='Do not read user config folder.')

parser.add_argument('--no-pygments', default=False,
            action="store_true",
            help='Do not use Pygments library for syntax hilighting even if available.')

parser.add_argument("files", default=None,
            help="List of files to Open.", 
            nargs='*') 

cmdline = parser.parse_args()

########    UPDATE CONGIGURATION    ##################################

global_config.DONT_USE_PYGMENTS_LIB = cmdline.no_pygments
global_config.DONT_USE_USER_CONFIG = cmdline.no_user_config
global_config.DEBUG = cmdline.debug

if not global_config.USER_DIR.exists() and not global_config.DONT_USE_USER_CONFIG:
    global_config.USER_DIR.mkdir()

########    SIGNAL HANDLING    #######################################

#from signal import signal, SIGWINCH, SIGINT
#
#signal(SIGWINCH, lambda a, b: Editor.show_screen(False))


########    DEBUG MODE     ###########################################

#if cmdline.debug:
    #""" Be Aware that debug mode is buggy !!! """
    #import sys
    #from pprint import pp
    #import faulthandler
#
    #def dump_infos(a, b):
        #Editor.screen.original_screen()
        #sys.stdout.flush()
        #items = [ Editor.current_buffer, 
                #Editor.screen, Editor.cache, Editor.registr ]
        #for item in items:
            #pp(item.__dict__)
            #input(repr(item) + 'ok?  ')
        #print(repr(a) + 'ok?  ')
        #print(repr(b) + 'ok?  ')
        #faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
        #sys.stdin.readline()
    #signal(SIGINT, dump_infos)
#
#
#########    START THE EDITOR #########################################

from vy.editor import _Editor as Editor
from sys import exit

Editor = Editor(*cmdline.files, command_line=cmdline)

if cmdline.profile:
    import cProfile, pstats, io
    from pstats import SortKey
    pr = cProfile.Profile()

    pr.enable()
    Editor(mode=cmdline.mode)
    pr.disable()

    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    with open('stats.LOG', 'w+') as out_file:
        print(s.getvalue(), file=out_file)
else:
    exit(Editor(mode=cmdline.mode))

