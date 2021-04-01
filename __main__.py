from pathlib import Path
from .editor import Editor

if __name__ == '__main__':
    def argv_parser():
        from argparse import ArgumentParser
        parser = ArgumentParser(prog='Vy',description='Legacy-free Vi-like editor')
        parser.add_argument("files", help="List of files to Open.",nargs='*',default=None)
        return parser.parse_args()

    conf_path = Path('~/.vym/').expanduser()
    if not conf_path.exists():
        conf_path.mkdir()

    Editor = Editor(*argv_parser().files)
    Editor()

else:
    Editor = Editor()

