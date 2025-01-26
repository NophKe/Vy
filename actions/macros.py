from vy.actions.helpers import sa_commands as _sa_commands

@_sa_commands(".")
def repeat_last_action(editor, reg=None, part=None, arg=None, count=1):
    editor._macro_keys.extend(eval(editor.registr['.']))

@_sa_commands("q")
def record_macro(editor, reg=None, part=None, arg=None, count=1):
    if not editor.record_macro:
        editor.screen.minibar("choose a letter for this new macro")
        editor.record_macro = editor.read_stdin()
        editor.screen.minibar(f"recording macro: «{editor.record_macro}»")
    else:
        editor.screen.minibar(f"end recording: «{editor.record_macro}»")
        editor.macros[editor.record_macro].pop()  # delete final 'q'
        editor.record_macro = ""

@_sa_commands("@")
def execute_macro(editor, reg=None, part=None, arg=None, count=1):
    macro_name = editor.read_stdin()
    try:
        macro = editor.macros[macro_name]
    except KeyError:
        raise editor.MustGiveUp(f" ( not a valid macro ) ")
    
    editor.screen.minibar(f"executing: «{editor.record_macro}»")
    editor.macros['@'] = editor.macros[macro_name]
    editor._macro_keys = macro.copy()

