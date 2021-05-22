from . import global_config

if __name__ == '__main__':
    from pathlib import Path

    def argv_parser():
        from argparse import ArgumentParser, BooleanOptionalAction
        parser = ArgumentParser(prog='Vy',description='Legacy-free Vi-like editor')
        parser.add_argument('--pygments', action=BooleanOptionalAction, default=True,
                            help='Use Pygments library for syntax hilighting if available')
        parser.add_argument("files", help="List of files to Open.",nargs='*',default=None)
        return parser.parse_args()
    cmdline = argv_parser()

    if not cmdline.pygments:
        global_config.DONT_USE_PYGMENTS_LIB = True

    conf_path = Path('~/.vym/').expanduser()
    if not conf_path.exists():
        conf_path.mkdir()
    
#Imports are late due to global variable reading from other modules
    from .editor import Editor
    Editor = Editor(*cmdline.files, command_line=cmdline)
    Editor()

else:
    from .editor import Editor
    Editor = Editor()

