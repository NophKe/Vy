from importlib import reload as _reload

def exc(ed):
	raise MemoryError('got it?')

def reload(ed):
	for buff in ed.cache:
		if '/vy/' in str(buff.path):
			try:
				buff.save()
			except:
				pass
	reload_debug(ed)
	reload_actions(ed)
	reload_interface(ed)
	reload_screen(ed)
	ed.screen.minibar('done!')

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
	_reload(with_arg)
	_reload(edition)
	_reload(helpers)
	_reload(motions)
	_reload(mode_change)
	_reload(commands)
	_reload(actions)
	ed._init_actions()

def version(ed):
	ed.warning('second')

def reload_debug(ed):
	from vy import debug_tools
	_reload(debug_tools)

def reload_interface(ed):
	from vy import interface
	interface = _reload(interface)
	ed.interface = interface.Interface(ed)

