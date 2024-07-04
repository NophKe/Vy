from vy.filetypes.textfile import TextFile

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
                grammar = parso.load_grammar()
                try:
                    parsed = grammar.parse(string, error_recovery=False)
                    for err in grammar.iter_errors(parsed):
                        ns[string] = f'(lexical error) line {err.start_pos[0] - 1}: {err.message} '
                        break
                    else:
                        ns[string] = ''
                except parso.ParserSyntaxError as err:
                    ns[string] = f'(parsing error) line {err.error_leaf.start_pos[0] - 1}: {err.message} '
            return ns[string]

        @property
        def footer(self):
            if syntax_err := self._has_syntax_errors():
                return syntax_err + super().footer
            return super().footer
        

try:
    from vy.global_config import DONT_USE_JEDI_LIB
    if DONT_USE_JEDI_LIB:
        raise ImportError
    
    from jedi import Script
    from jedi.api.exceptions import RefactoringError
except ImportError:
    pass
else:
    def DO_goto_declaration_under_cursor(editor, *args, **kwargs):
        curbuf: PyFile = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        result = engine.goto(line=lin+1, column=col)
        if not result:
            editor.screen.minibar('no match found!')
        elif len(result) == 1:
            res = result[0]    
            if res.module_path != curbuf.path:
                editor.edit(res.module_path)
            if position := res.get_definition_start_position():
                new_lin, new_col = position
                curbuf.cursor_lin_col = new_lin-1, new_col+1 
        else:
            editor.screen.minibar('too many matches.')
    
    def DO_get_object_and_class(editor, *args, **kwargs):
        curbuf: PyFile = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        results = engine.help(line=lin+1, column=col)
        if not results:
            editor.screen.minibar('no help found!')
        elif len(results) == 1:
            editor.warning(repr(results[0]))
        else:
            editor.screen.minibar('ambiguous symbol or multiple results')
            
    def DO_extract_as_new_variable(editor, arg=None, **kwargs):
        if arg:
            curbuf: PyFile = editor.current_buffer
            lin, col = curbuf.cursor_lin_col
            engine: Script = curbuf.jedi()
            try:
                result = engine.extract_variable(line=lin+1, column=col, new_name=arg)
            except RefactoringError as err:
                editor.warning(str(err))
            else:
                for path, new_version in changes.items():
                    editor.cache[path].string = new_version.get_new_code()
                    changes = result.get_changed_files()[None].get_new_code()
        else:
            editor.warning('(bad syntax, no name provided)  :command {name}')
        
    def DO_inline_current_expression(editor, arg=None, **kwargs):
        curbuf: PyFile = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        try:
            result = engine.inline(line=lin+1, column=col)
        except RefactoringError as err:
            editor.warning(str(err))
        else:
            changes = result.get_changed_files()
            for path, new_version in changes.items():
                editor.cache[path].string = new_version.get_new_code()
    
    def DO_extract_as_new_function(editor, arg=None, **kwargs):
        if arg:
            curbuf: PyFile= editor.current_buffer
            lin, col = curbuf.cursor_lin_col
            engine: Script = curbuf.jedi()
            try:
                result = engine.extract_function(line=lin+1, column=col, new_name=arg)
            except RefactoringError as err:
                editor.warning(str(err))
            else:
                for path, new_version in changes.items():
                    editor.cache[path].string = new_version.get_new_code()
                    changes = result.get_changed_files()[None].get_new_code()
        else:
            editor.warning('(bad syntax, no name provided)  :command {name}')
    
    def DO_rename_symbol_under_cursor(editor, arg=None, **kwargs):
        if arg:
            curbuf: PyFile = editor.current_buffer
            lin, col = curbuf.cursor_lin_col
            engine: Script = curbuf.jedi()
            try:
                result = engine.rename(line=lin+1, column=col, new_name=arg)
            except RefactoringError as err:
                editor.warning(str(err))
            else:
                changes = result.get_changed_files()
                for path, new_version in changes.items():
                    editor.cache[path].string = new_version.get_new_code()
                editor.screen.minibar(f'{len(changes)} file(s) modified.')
        else:
            editor.warning('(bad syntax, no name provided)  :command {name}')
        
    def DO_get_help(editor, arg=None, **kwargs):
        curbuf: PyFile = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        result = engine.infer(line=lin+1, column=col)
        if result:
            doc = result[0].docstring(fast=False)
            editor.screen.minibar(*doc.splitlines())
        else:
            editor.warning(' (no help available)')
     
    class PyFile(PyFile):
        PyFile.actions[':goto_declaration'] = DO_goto_declaration_under_cursor
        PyFile.actions['gd']                = DO_goto_declaration_under_cursor
        PyFile.actions[':get_object_and_class'] = DO_get_object_and_class 
        PyFile.actions[':extract_as_new_variable'] = DO_extract_as_new_variable
        PyFile.actions[':inline_current_expression'] = DO_inline_current_expression
        PyFile.actions[':extract_as_new_function'] = DO_extract_as_new_function
        PyFile.actions[':rename_symbol_under_cursor'] = DO_rename_symbol_under_cursor
        PyFile.actions[':get_help'] = DO_get_help
        PyFile.actions['K']         = DO_get_help

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
                           
        def jedi(self, ns={}) -> Script:
            # AGAIN jedi is not thread-safe... THIS should be LOCKED !
            if self.string not in ns:
                ns[self.string] = Script(code=self.string, path=self.path)
            return ns[self.string]
            
        def _token_chain(self):
            engine: Script = self.jedi()
            lin,col = self.cursor_lin_col
            if self.current_line[col] != '\n':
                result = engine.infer(line=lin+1, column=col)
                if result:
                    assert len(result) == 1
                    token = result[0]
                return token
        
        @property
        def footer(self):
            parsing_and_saving = super().footer
            # if in those exact states, there is no syntax error
            if ' ( oldest state )' == parsing_and_saving:
                return 'You are a jedi.'
            if ' ( saved )' == parsing_and_saving:
                return 'May the Force be with you.'
            return parsing_and_saving


try:
    from black import format_str, Mode
except ImportError:
    pass
else:
    default_mode = Mode(line_length=120)
    
    def DO_reformat_whole_file(editor, reg=None, part=None, arg=None, count=1):
        cb = editor.current_buffer
        cb.string = format_str(cb.string, mode=default_mode)
        
    def DO_reformat_selection(editor, reg=None, part=None, arg=None, count=1):
        cb = editor.current_buffer
        lines = cb.splited_lines.copy()
        selection = editor.current_buffer.selected_lines
        selected_str = ''.join(lines[chosen] for chosen in selection)
        new_value = format_str(selected_str, mode=default_mode)
        cb[cb.selected_lines_off] = new_value
    
    class PyFile(PyFile):
        PyFile.actions[':reformat_whole_file'] = DO_reformat_whole_file
        PyFile.actions[':reformat_selection'] = DO_reformat_selection

