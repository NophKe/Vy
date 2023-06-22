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

parser.add_argument('--no-jedi', default=False,
            action="store_true",
            help='Do not use Jedi library for code completion even if available.')

parser.add_argument('--command', default='',
            type=str,
            help='Screen shows selected infos and enter the debugger.')

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

from signal import signal, SIGWINCH, SIGUSR1, raise_signal
import threading
import sys

########    DEBUG MODE     ###########################################

#def dump_infos(a, b):
    #from __main__ import Editor
    #from os import system
    #from pprint import pp
    #import faulthandler
    #try:
        #Editor.screen.original_screen()
    #except AttributeError:
        #pass
    #try:
        #Editor.stop_async_io()
    #except:
        #pass
    #faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
    #breakpoint()
    #raise Editor.exception


def enter_debugger():
    try: Editor.stop_async_io()
    except: pass
    sys.__breakpointhook__()
sys.breakpointhook = enter_debugger

def retrive_exc_in_main_thread(a, b):
    assert Editor.exception.exc_value, "Received signal but no exception"
    if Editor._async_io_flag:
        try: Editor.stop_async_io()
        except: pass
    exc = Editor.exception
    import sys
    from traceback import print_tb
    type_, value_, trace_ = sys.exc_info()
    print(Editor.screen.infobar_txt)
    print(  'The following *unhandled* exception was encountered:\n'
           f'  >  {repr(exc)} indicating:\n'
           f'  >  {str(exc)}\n')
    print_tb(trace_)
    exit(1)
signal(SIGUSR1, retrive_exc_in_main_thread)

def raise_unraisable(unraisable):
    Editor.exception = unraisable
    raise_signal(SIGUSR1)
threading.excepthook = raise_unraisable

#sys.unraisablehook = raise_unraisable
from vy.editor import _Editor as Editor
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
    exit()

if cmdline.command:
    Editor.push_macro(cmdline.command)
    
Editor(mode=cmdline.mode)

