#!/usr/bin/python3 -m
"""
This file is the main entry point for the Vy Editor and is not supposed 
to be executed outside the Vy package. This module is in charge of basic
initialization.

This software is meant to be used on any modern linux platform and will
try to perform a few sanity checks about your configuration, then parse
the command line arguments and update the vy.global_config module 
accordingly.

It will then create the vy._Editor instance and will start the main loop
and begin user interaction.

To see all available option on command line, use:

 python -m vy --help

"""

#######   BASIC INITIALISATION

if __name__ != '__main__' or __package__ != 'vy':
    raise ImportError(
    'This file is the main entry point for the Vy Editor and '
    'is not supposed to be imported, but executed by: python -m vy')

#######    SANITY CHECKS

# Required dependency from standard library, if those are not present,
# on current setup, we just let the ImportError exception propagate. 

from argparse import ArgumentParser 
from sys import stdin, stdout, exit

if not (stdin.isatty() and stdout.isatty()):
    exit('VY FATAL ERROR: stdin or stdout is not a terminal.')

########   COMMAND LINE PARSING #############################

parser = ArgumentParser(prog='Vy',
                        description='LEGACY-FREE VI-LIKE EDITOR',
                        epilog='\n----\n',
                        )

parser.add_argument('--debug', default=False,
            action="store_true",
            help='Screen shows selected infos and enter the debugger.')

parser.add_argument('--no-user-config', default=False,
            action="store_true",
            help='Do not read user config folder.')

parser.add_argument('--no-pygments', default=False,
            action="store_true",
            help='Do not use Pygments library for syntax hilighting even if available.')

parser.add_argument('--no-jedi', default=False,
            action="store_true",
            help='Do not use Jedi library for code completion even if available.')

parser.add_argument("files", default=None,
            help="List of files to Open.", 
            nargs='*') 

cmdline = parser.parse_args()

########    UPDATE CONGIGURATION    ##################################

from vy import global_config

global_config.DONT_USE_USER_CONFIG = cmdline.no_user_config

if not global_config.DONT_USE_USER_CONFIG:
    global_config._source_config()

global_config.DONT_USE_PYGMENTS_LIB = cmdline.no_pygments
global_config.DONT_USE_JEDI_LIB = cmdline.no_jedi
global_config.DEBUG = cmdline.debug


########    SIGNAL HANDLING    #######################################

from signal import signal, raise_signal, SIGKILL
import faulthandler
import threading
import sys
import traceback

def enter_debugger():
    try: Editor.stop_async_io()
    except: pass
    sys.__breakpointhook__()
sys.breakpointhook = enter_debugger

def raise_unraisable(unraisable):
    try:
        global Editor
        Editor = Editor
    except NameError:
        print('fatal error before Editor got inititalized !')
    else:
        Editor.screen.original_screen()
        Editor.screen.show_cursor()
        try:
            Editor.stop_async_io()
        except BaseException as exc:
            print(exc)

    from traceback import print_tb
    print(  'The following *unhandled* exception was encountered:\n'
           f'  >  {str(unraisable.exc_type)} indicating:\n'
           f'  >  {unraisable.exc_value}\n')
    print_tb(unraisable.exc_traceback)
    print()
    faulthandler.dump_traceback(all_threads=True)
    print()
    raise_signal(SIGKILL)
threading.excepthook = raise_unraisable


print('Vy is starting.')

from vy.editor import _Editor
Editor = _Editor(*cmdline.files, command_line=cmdline)
Editor()

print('Thanks for using Vy in its beta version.\n'
      'Any comment or issue posted on github.com/nophke/vy will be taken into account.')
