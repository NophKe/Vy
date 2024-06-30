from vy.filetypes.textfile import TextFile
from jedi.api.refactoring import ChangedFile

class SimplePyFile(TextFile):
    actions = {} # new empty dict to avoid poluting the inherited
                 # one from TextFile base class.
    set_wrap = False   
    set_autoindent = True
    set_expandtabs = True
    set_number = True
    set_comment_string = ('#', '')

try:
    import parso
except ImportError:
    class PyFile(SimplePyFile):
        pass
else:
    class PyFile(SimplePyFile):
        def _has_syntax_errors(self, ns={}):
            string = self.string
            if string not in ns:
                import parso
                grammar = parso.load_grammar()
                try:
                    parsed = grammar.parse(string, error_recovery=False)
                    for err in grammar.iter_errors(parsed):
                        ns[string] = f'(found error) line {err.start_pos[0] - 1}: {err.message} '
                        break
                    else:
                        ns[string] = ''
                except parso.ParserSyntaxError as err:
                    ns[string] = f'(parsing error) line {err.error_leaf.start_pos[0] - 1}: {err.message} '
            return ns[string]

        @property
        def footer(self):
            return self._has_syntax_errors() or '' + super().footer

try:
    import jedi
except ImportError:
    pass
else:
#    from vy.editor import _Editor
    from jedi import Script
    from jedi.api.exceptions import RefactoringError
    
    def DO_goto_declaration_under_cursor(editor, *args, **kwargs):
        curbuf = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        result = engine.goto(line=lin+1, column=col-1)
        if not result:
            editor.screen.minibar('no match found!')
        elif len(result) == 1:
            new_lin, new_col = result[0].get_definition_start_position()
            editor.current_buffer.cursor_lin_col = new_lin-1, new_col+1 
        else:
            editor.screen.minibar('too many matches.')
    
    def DO_get_object_and_class(editor, *args, **kwargs):
        curbuf = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        results = engine.help(line=lin+1, column=col-1)
        if not results:
            editor.screen.minibar('no help found!')
        elif len(results) == 1:
            editor.warning(repr(results[0]))
        else:
            editor.screen.minibar('ambiguous symbol or multiple results')
            
    def DO_extract_as_new_variable(editor, arg=None, **kwargs):
        if arg:
            curbuf = editor.current_buffer
            lin, col = curbuf.cursor_lin_col
            engine: Script = curbuf.jedi()
            try:
                result = engine.extract_variable(line=lin+1, column=col-1, new_name=arg)
            except RefactoringError:
                editor.warning('nope dont work.')
            else:
                changes = result.get_changed_files()[None].get_new_code()
                editor.current_buffer.string = changes
        else:
            editor.warning('(bad syntax, no name provided)  :command {name}')
        
    def DO_inline_current_expression(editor, arg=None, **kwargs):
        curbuf = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        try:
            result = engine.inline(line=lin+1, column=col-1)
        except RefactoringError:
            editor.warning('nope dont work.')
        else:
            changes = result.get_changed_files()[None].get_new_code()
            editor.current_buffer.string = changes
    
    def DO_extract_as_new_function(editor, arg=None, **kwargs):
        if arg:
            curbuf = editor.current_buffer
            lin, col = curbuf.cursor_lin_col
            engine: Script = curbuf.jedi()
            try:
                result = engine.extract_function(line=lin+1, column=col-1, new_name=arg)
            except RefactoringError:
                editor.warning('nope dont work.')
            else:
                changes = result.get_changed_files()[None].get_new_code()
                editor.current_buffer.string = changes
        else:
            editor.warning('(bad syntax, no name provided)  :command {name}')
    
    def DO_rename_symbol_under_cursor(editor, arg=None, **kwargs):
        if arg:
            curbuf = editor.current_buffer
            lin, col = curbuf.cursor_lin_col
            engine: Script = curbuf.jedi()
            try:
                result = engine.rename(line=lin+1, column=col-1, new_name=arg)
            except RefactoringError:
                editor.warning('nope dont work.')
            else:
                changes = result.get_changed_files()[None].get_new_code()
                editor.current_buffer.string = changes
        else:
            editor.warning('(bad syntax, no name provided)  :command {name}')
        
    def DO_get_help(editor, arg=None, **kwargs):
        curbuf = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        result = engine.infer(line=lin+1, column=col-1)
        if result:
            doc = result[0].docstring(fast=False)
            editor.screen.minibar(*doc.splitlines())
        else:
            editor.warning(' (no help available)')
     
    class PyFile(PyFile):
        PyFile.actions[':goto_declaration'] = DO_goto_declaration_under_cursor
        PyFile.actions[':get_object_and_class'] = DO_get_object_and_class 
        PyFile.actions[':extract_as_new_variable'] = DO_extract_as_new_variable
        PyFile.actions[':inline_current_expression'] = DO_inline_current_expression
        PyFile.actions[':extract_as_new_function'] = DO_extract_as_new_function
        PyFile.actions[':rename_symbol_under_cursor'] = DO_rename_symbol_under_cursor
        PyFile.actions[':get_help'] = DO_get_help

        # if we reache this line then jedi install 
        # is ok. parso is dependency of jedi then ._has_syntax_errors and .footer are
        # defined. No need to redefine PyFile.footer! 
        #
        # But still redefine _has_syntax_errors to make profit of jedi caching system
        #
        
#        def _has_syntax_errors(self, ns={}):
#            string = self.string
#            if string not in ns:
#                engine: Script = self.jedi()
#                errors = engine.get_syntax_errors()          
#                if errors:
#                    error_message = errors[0].get_message()
#                    ns[string] = error_message
#                    return error_message
#                ns[string] = ''
#            return ns[string]
        #
        # jedi is not thread-safe... I forgot one more time...
        # 
                           
        def jedi(self, ns={}):
            # AGAIN jedi is not thread-safe... THIS should be LOCKED !
            if self.string not in ns:
                from jedi import Script
                ns[self.string] = Script(code=self.string,)
            return ns[self.string]

