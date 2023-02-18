from code import InteractiveConsole
from vy.interface.helpers import Completer
from __main__ import __dict__ as global_dict
from vy.filetypes.textfile import TextFile
from pathlib import Path # TODO delete this import

header = 'from vy import Editor\n'
def loop(editor):

    class Console(InteractiveConsole):
        def write(self, text):
            text = text.splitlines()
            if text:
                editor.screen.minibar(*text)

    class Readline(Completer):
        def get_complete(self):
            source = TextFile(init_text=header+self.buffer.string,
                              cursor=len(header)+self.buffer.cursor -1,
                              path=Path('fake.py')
                              )
            return source.get_completions()
            
    locals_dict = {'vy': editor}

    readline = Readline('ex_history', '>>> ', editor,completion_dict=global_dict )
    console = Console(locals=global_dict)
    line = readline()

    while console.push(line):
        if console.buffer:
            screen = ['>>> ' + val for val in console.buffer]
        else:
            screen = []
        #editor.screen.minibar(screen)
        line = readline(buffered=screen)

    return 'normal'

