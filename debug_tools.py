"""
This module contains un-documented actions accessible with the :debug
commands.  Those commands may change any time, and no documentation than
reading this module source file will be provided.
If used with no argument :debug will try to reload as much of the editor
as it is capable of.
"""
from importlib import reload as _reload

def last_ex(ed):
	if (last_ex_cmd := ed.registr['>']) and '\n' not in last_ex_cmd:
		from vy.global_config import USER_DIR
		(USER_DIR / "debugging_values").write_text(last_ex_cmd)
		
def test_screen(ed):
    for x in range(20):
        ed.screen.clear_screen()
        print(x)
        import time
        time.sleep(0.5)
    	
def no_screen(ed):
	ed.screen.clear_screen()

def debug(ed):
	breakpoint()
	
def exc(ed):
	raise MemoryError('got it?')

def reload(ed):
	for buff in ed.cache:
		try: 	buff.save()
		except: pass
	from vy import debug_tools
	_reload(debug_tools)
	
	reload_actions(ed)
	reload_filetypes(ed)
	reload_interface(ed)
	reload_screen(ed)
	reload_cache(ed)
	
	reload_editor(ed)
	ed.screen.minibar('( reloaded ! )')
	
def reload_editor(ed):
	from vy import editor
	pass

def reload_screen(ed):
	from vy import screen
	ed.stop_async_io()
	screen = _reload(screen)
	ed.screen = screen.Screen(ed.current_buffer)
	ed.start_async_io()

def reload_actions(ed):
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
	ed._init_actions()
	ed.actions.normal['zz'](ed)
	
def reload_interface(ed):
	from vy import interface
	interface = _reload(interface)
	ed.interface = interface.Interface(ed)

def reload_filetypes(ed):
	from vy.filetypes import basefile
	from vy.filetypes import folder
	from vy.filetypes import textfile
	from vy import filetypes
	_reload(filetypes)
	_reload(basefile)
	_reload(folder)
	_reload(textfile)

def reload_cache(ed):
	from vy import editor
	new = _reload(editor)
	ed.cache = new._Cache()
	for k, v in ed.cache._dic:
		ed.cache[k]

