"""
This module contains un-documented actions accessible with the :debug
commands.  Those commands may change any time, and no documentation than
reading this module source file will be provided.
If used with no argument :debug will try to reload as much of the editor
as it is capable of.
"""

# This file mixes spaces and tabs jus for confusing Vy set_autoindent
# option and spot any regression while reloading.

from importlib import reload as _reload

def last_ex(ed):
	if (last_ex_cmd := ed.registr['>']) and '\n' not in last_ex_cmd:
		from vy.global_config import USER_DIR
		(USER_DIR / "debugging_values").write_text(last_ex_cmd)
		ed.edit(USER_DIR / "debugging_values")
		
def test_screen(ed):
    for x in range(20):
        ed.screen.clear_screen()
        print(x)
        import time
        time.sleep(0.5)

def exit(ed):
    raise SystemExit

def quit(ed):
    raise BaseException 

def no_screen(ed):
	ed.screen.clear_screen()

def debug(ed):
	breakpoint()
	
def exc(ed):
	raise MemoryError('got it?')

def reload(ed):
	from vy import actions
	from vy.actions import helpers
	from vy.actions import motions
	from vy.actions import mode_change
	from vy.actions import commands
	from vy.actions import edition
	from vy.actions import with_arg
	from vy.actions import linewise
	_reload(linewise)
	_reload(with_arg)
	_reload(edition)
	_reload(helpers)
	_reload(motions)
	_reload(mode_change)
	_reload(commands)
	_reload(actions)

