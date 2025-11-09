from vy.filetypes.textfile import TextFile
from vy.filetypes import _register_extension
from functools import lru_cache

@_register_extension('.py')
class SimplePyFile(TextFile):
    actions = {}
    # new empty dict to avoid poluting the inherited
    # one from TextFile base class.
    
    set_wrap = False
    set_autoindent = True
    set_expandtabs = True
    set_number = True
    set_comment_string = ('#', '')
    _lsp_server = ['pylsp', '-v']
    _lsp_server = ['pylsp']
    _lsp_lang_id = 'python'

    def lexer(self, code):
        KEYWORDS = {
            "False","None","True","and","as","assert","async","await","break","class","continue",
            "def","del","elif","else","except","finally","for","from","global","if","import",
            "in","is","lambda","nonlocal","not","or","pass","raise","return","try","while","with","yield"
        }

        MAGIC_NAMES = {
            "__init__","__new__","__del__","__repr__","__str__","__bytes__","__format__","__lt__",
            "__le__","__eq__","__ne__","__gt__","__ge__","__hash__","__bool__","__getattr__",
            "__getattribute__","__setattr__","__delattr__","__dir__","__len__","__getitem__",
            "__setitem__","__delitem__","__iter__","__next__","__reversed__","__contains__",
            "__add__","__sub__","__mul__","__matmul__","__truediv__","__floordiv__","__mod__",
            "__divmod__","__pow__","__lshift__","__rshift__","__and__","__xor__","__or__",
            "__radd__","__rsub__","__rmul__","__rmatmul__","__rtruediv__","__rfloordiv__",
            "__rmod__","__rdivmod__","__rpow__","__rlshift__","__rrshift__","__rand__","__rxor__",
            "__ror__","__iadd__","__isub__","__imul__","__imatmul__","__itruediv__","__ifloordiv__",
            "__imod__","__ipow__","__ilshift__","__irshift__","__iand__","__ixor__","__ior__",
            "__neg__","__pos__","__abs__","__invert__","__complex__","__int__","__float__",
            "__index__","__round__","__trunc__","__floor__","__ceil__","__enter__","__exit__",
            "__call__","__await__","__aiter__","__anext__","__aenter__","__aexit__","__copy__",
            "__deepcopy__","__missing__","__reduce__","__reduce_ex__","__sizeof__","__subclasshook__",
            "__init_subclass__","__class_getitem__","__prepare__","__instancecheck__","__subclasscheck__",
            "__set_name__","__main__"
        }

        BUILTINS = {
            "abs","all","any","ascii","bin","bool","breakpoint","bytearray","bytes","callable","chr",
            "classmethod","compile","complex","delattr","dict","dir","divmod","enumerate","eval","exec",
            "filter","float","format","frozenset","getattr","globals","hasattr","hash","help","hex","id",
            "input","int","isinstance","issubclass","iter","len","list","locals","map","max","memoryview",
            "min","next","object","oct","open","ord","pow","print","property","range","repr","reversed",
            "round","set","setattr","slice","sorted","staticmethod","str","sum","super","tuple","type",
            "vars","zip","__import__","NotImplemented","Ellipsis","exit","quit"
        }

        OPERATORS = {
            "+","-","*","**","/","//","%","@","<<",">>", "&","|","^","~",
            ":=","<",">","<=",">=","==","!="
        }

        PUNCT = set("()[]{}.,:;@=->")
    
        i, n = 0, len(code)
        indents = [0]
        newline_pending = False
    
        def peek(k=0):
            return code[i + k] if i + k < n else ''
    
        def emit_indent_dedent(curr_indent, line_start):
            nonlocal indents
            if curr_indent > indents[-1]:
                indents.append(curr_indent)
                yield (line_start, "", "")
                #indent
            else:
                while curr_indent < indents[-1]:
                    indents.pop()
                    yield (line_start, "", "")
                    #dedent
    
        while i < n:
            c = code[i]
            
            if c == '\\' and peek(1) == '\n':
                start = i
                i += 2
                yield (start, "", "\\\n")
                continue

            # --- newlines ---
            if c == '\n':
                yield (i, "", "\n")
                #newline
                i += 1
                newline_pending = True
                continue
    
            # --- spaces (and detect indent level at start of line) ---
            if c in ' \t' and (i == 0 or code[i-1] == '\n'):
                start = i
                while i < n and code[i] in ' \t':
                    i += 1
                indent_width = i - start
                for tok in emit_indent_dedent(indent_width, start):
                    yield tok
                yield (start, "", code[start:i])
                continue
    
            if c in ' \t\r':
                start = i
                while i < n and code[i] in ' \t\r':
                    i += 1
                yield (start, "", code[start:i])
                #whitespace
                continue
    
            # --- comments ---
            if c == '#':
                start = i
                while i < n and code[i] != '\n':
                    i += 1
                yield (start, "Token.Comment", code[start:i])
                continue
    
            # --- string or f-string ---
            if c in ('"', "'") or (c in 'fF' and peek(1) in ('"', "'")):
                start = i
                prefix = ''
                if c in 'fF':
                    prefix = c
                    i += 1
                    c = peek()
                quote = c
                triple = code[i:i+3] == quote*3
                if triple: i += 3
                else: i += 1
                while i < n:
                    if triple and code[i:i+3] == quote*3:
                        i += 3
                        break
                    elif not triple and code[i] == quote:
                        i += 1
                        break
                    elif code[i] == '\\' and i + 1 < n:
                        i += 2
                    else:
                        i += 1
                yield (start, "Token.Literal.String", code[start:i])
                continue
    
            # --- numbers ---
            if c.isdigit() or (c == '.' and peek(1).isdigit()):
                start = i
                if c == '0' and peek(1) in 'xXbBoO':
                    i += 2
                    while i < n and (code[i].isalnum() or code[i] == '_'):
                        i += 1
                else:
                    has_dot = False
                    while i < n and (code[i].isdigit() or code[i] in "._eE+-jJ"):
                        if code[i] == '.':
                            if has_dot: break
                            has_dot = True
                        i += 1
                yield (start, "Token.Literal.Number", code[start:i])
                continue
    
            # --- identifier / keyword ---
            if c.isalpha() or c == '_':
                start = i
                while i < n and (code[i].isalnum() or code[i] == '_'):
                    i += 1
                val = code[start:i]

                if val in KEYWORDS:
                    yield (start, "Token.Keyword", val)
                elif val in MAGIC_NAMES:
                    yield (start, "Token.Name.Builtin", val)
                elif val in BUILTINS:
                    yield (start, "Token.Name.Builtin", val)
                else:
                    yield (start, "Token.Name", val)
                continue
            # --- operator ---
            two = code[i:i+2]
            three = code[i:i+3]
            if three in OPERATORS:
                yield (i, "Token.Operator", three)
                i += 3
                continue
            elif two in OPERATORS:
                yield (i, "Token.Operator", two)
                i += 2
                continue
            elif c in OPERATORS:
                yield (i, "Token.Operator", c)
                i += 1
                continue
    
            # --- punctuation ---
            if c in PUNCT:
                yield (i, "Token.Operator", c)
                i += 1
                continue
    
            # --- unknown ---
            yield (i, "Token.Error", c)
            i += 1
    
        # --- EOF cleanup ---
        for tok in emit_indent_dedent(0, n):
            yield tok
        yield (n, "", "")
        #eof

try:
    import parso
except ImportError:
    @_register_extension('.py')
    class PyFile(SimplePyFile):
        pass
else:
    @_register_extension('.py')
    class PyFile(SimplePyFile):
        def _has_syntax_errors(self):
            if self._async_tasks.must_stop:
                return '( not parsed, no async )'
            if string := self._string:
                return self._cached_has_syntax_errors(string)
            return '( not parsed, no value )'

        @lru_cache(127)
        def _cached_has_syntax_errors(self, string):
            grammar = parso.load_grammar()
            try:
                parsed = grammar.parse(string, error_recovery=False)
                for err in grammar.iter_errors(parsed):
                    return f'( lexical error! line {err.start_pos[0] - 1}: {err.message} )'
            except parso.ParserSyntaxError as err:
                return f'( parsing error! line {err.error_leaf.start_pos[0] - 1}: {err.message} )'
            return '( no syntax error )'

        @property
        def footer(self):
            return self._has_syntax_errors() + super().footer


try:
    from vy.global_config import DONT_USE_JEDI_LIB

    if DONT_USE_JEDI_LIB:
        raise ImportError

    from jedi import Script
    from jedi import Interpreter
    from jedi.api.exceptions import RefactoringError
    from jedi import settings
    
    settings.add_bracket_after_function = True
    settings.case_insensitive_completion = True
#    settings.fast_parser = False

except ImportError:
    pass
else:
    def DO_goto_declaration_under_cursor(editor, *args, **kwargs):
        curbuf: PyFile = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        result = engine.goto(line=lin + 1, column=col)
        if not result:
            editor.screen.minibar('no match found!')
        elif len(result) == 1:
            res = result[0]
            if res.module_path != curbuf.path:
                editor.edit(res.module_path)
            if position := res.get_definition_start_position():
                new_lin, new_col = position
                curbuf.cursor_lin_col = new_lin - 1, new_col + 1
                editor.actions.normal('zz')
        else:
            editor.screen.minibar('too many matches.')

    def DO_get_object_and_class(editor, *args, **kwargs):
        curbuf: PyFile = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        results = engine.help(line=lin + 1, column=col)
        if not results:
            editor.screen.minibar('no help found!')
        elif len(results) == 1:
            editor.warning(repr(results[0]))
        else:
            editor.screen.minibar('ambiguous symbol or multiple results')

    def DO_extract_as_new_variable(editor, arg=None, **kwargs):
        if not arg:
            raise editor.MustGiveUp('(bad syntax, no name provided)    :command {name}')
        
        curbuf: PyFile = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        
        try:
            result = engine.extract_variable(line=lin + 1, column=col, new_name=arg)
        except RefactoringError as err:
            raise editor.MustGiveUp(str(err))
        
        changes = result.get_changed_files()
        for path, new_version in changes.items():
            editor.cache[path].string = new_version.get_new_code()
        editor.screen.minibar(f'{len(changes)} files modified')

    def DO_inline_current_expression(editor, arg=None, **kwargs):
        curbuf: PyFile = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        try:
            result = engine.inline(line=lin + 1, column=col)
        except RefactoringError as err:
            raise editor.MustGiveUp(str(err))
        
        changes = result.get_changed_files()
        for path, new_version in changes.items():
            editor.cache[path].string = new_version.get_new_code()
        editor.screen.minibar(f'{len(changes)} files modified')

    def DO_extract_as_new_function(editor, arg=None, **kwargs):
        if arg:
            curbuf: PyFile = editor.current_buffer
            lin, col = curbuf.cursor_lin_col
            engine: Script = curbuf.jedi()
            try:
                result = engine.extract_function(line=lin + 1, column=col, new_name=arg)
            except RefactoringError as err:
                editor.warning(str(err))
            else:
                changes = result.get_changed_files()
                for path, new_version in changes.items():
                    editor.cache[path].string = new_version.get_new_code()
        else:
            editor.warning('(bad syntax, no name provided)    :command {name}')

    def DO_rename_symbol_under_cursor(editor, arg=None, **kwargs):
        if arg:
            curbuf: PyFile = editor.current_buffer
            lin, col = curbuf.cursor_lin_col
            engine: Script = curbuf.jedi()
            try:
                result = engine.rename(line=lin + 1, column=col, new_name=arg)
            except RefactoringError as err:
                editor.warning(str(err))
            else:
                changes = result.get_changed_files()
                for path, new_version in changes.items():
                    editor.cache[path].string = new_version.get_new_code()
                editor.screen.minibar(f'{len(changes)} file(s) modified.')
        else:
            editor.warning('(bad syntax, no name provided)    :command {name}')

    def DO_get_help(editor, arg=None, **kwargs):
        curbuf: PyFile = editor.current_buffer
        lin, col = curbuf.cursor_lin_col
        engine: Script = curbuf.jedi()
        result = engine.infer(line=lin + 1, column=col)
        if result:
            doc = result[0].docstring(fast=False)
            if doc:
                editor.screen.minibar(*doc.splitlines())
            else:
                editor.screen.minibar(str(result[0]))
        else:
            editor.warning(' (no help available)')

    @_register_extension('.py')
    class PyFile(PyFile):
        PyFile.actions[':goto_declaration'] = DO_goto_declaration_under_cursor
        PyFile.actions['gd'] = DO_goto_declaration_under_cursor
        PyFile.actions[':get_object_and_class'] = DO_get_object_and_class
        PyFile.actions[':extract_as_new_variable'] = DO_extract_as_new_variable
        PyFile.actions[':inline_current_expression'] = DO_inline_current_expression
        PyFile.actions[':extract_as_new_function'] = DO_extract_as_new_function
        PyFile.actions[':rename_symbol_under_cursor'] = DO_rename_symbol_under_cursor
        PyFile.actions[':get_help'] = DO_get_help
        PyFile.actions['K'] = DO_get_help

        def jedi(self) -> Script:
            return Script(code=self.string, path=self.path)
            return Interpreter(code=self.string, path=self.path)

        def _token_chain(self):
            engine: Script = self.jedi()
            lin, col = self.cursor_lin_col
            if self.current_line[col] != '\n':
                result = engine.infer(line=lin + 1, column=col)
                if result:
                    assert len(result) == 1
                    token = result[0]
                    return token
            return False

        def auto_complete(self):
            engine: Script = self.jedi()
            try:
                lin, col = self.cursor_lin_col
                results = engine.complete(line=lin + 1, column=col - 1)
            except:
                return super().auto_complete()
                
            if results:
                lengh = results[0].get_completion_prefix_length()
                rv = [item.name_with_symbols for item in results]
                return rv, lengh
            return super().auto_complete()


try:
    from black import format_str, Mode
except ImportError:
    pass
else:
    default_mode = Mode(line_length=120, string_normalization=False)

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

    @_register_extension('.py')
    class PyFile(PyFile):
        PyFile.actions[':reformat_whole_file'] = DO_reformat_whole_file
        PyFile.actions[':reformat_selection'] = DO_reformat_selection


try:
    import mypy
    from mypy.main import main as mypy_checker
except:
    pass

