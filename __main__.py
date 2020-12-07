from .editor import Editor

if __name__ == '__main__':
    def argv_parser():
        from argparse import ArgumentParser
        parser = ArgumentParser(prog='Vy',description='Vee Why?')
        parser.add_argument("files", help="List of files to Open.",nargs='*',default=None)
        return parser.parse_args()

    Editor = Editor(*argv_parser().files)
    Editor()

else:
    Editor = Editor()

