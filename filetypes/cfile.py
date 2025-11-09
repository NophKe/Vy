from vy.filetypes.textfile import TextFile
from vy.filetypes import _register_extension

_register_extension('.c')
class CFile(TextFile):
    set_wrap = True
    set_autoindent = True
    set_expandtabs = True
    set_number = True
    set_comment_string = ('/*', '*/')
    
    _lsp_server = ['ccls']
    _lsp_lang_id = 'c'
    
    def lexer(self, code):
        KEYWORDS = {
            "auto","break","case","char","const","continue","default","do","double","else",
            "enum","extern","float","for","goto","if","inline","int","long","register",
            "restrict","return","short","signed","sizeof","static","struct","switch",
            "typedef","union","unsigned","void","volatile","while","_Bool","_Complex","_Imaginary"
        }
        OPERATORS = set("+-*/%<>=!&|^~")
        PUNCT = set("(){}[];,.?:")
    
        i, n = 0, len(code)
        while i < n:
            c = code[i]
    
            # --- newline ---
            if c == '\n':
                yield (i, "", "\n")
                i += 1
                continue
    
            # --- spaces ---
            if c in ' \t\r':
                start = i
                while i < n and code[i] in ' \t\r':
                    i += 1
                yield (start, "", code[start:i])
                continue
    
            # --- preprocessor ---
            if c == '#':
                start = i
                while i < n:
                    if code[i] == '\\' and i + 1 < n and code[i+1] == '\n':
                        i += 2
                        continue
                    if code[i] == '\n':
                        break
                    i += 1
                yield (start, "Token.Comment.Preproc", code[start:i])
                continue
    
            # --- comments ---
            if c == '/' and i + 1 < n and code[i+1] == '/':
                start = i
                i += 2
                while i < n and code[i] != '\n':
                    i += 1
                yield (start, "Token.Comment", code[start:i])
                continue
    
            if c == '/' and i + 1 < n and code[i+1] == '*':
                start = i
                i += 2
                while i < n - 1 and not (code[i] == '*' and code[i+1] == '/'):
                    i += 1
                i += 2
                yield (start, "Token.Comment", code[start:i])
                continue
    
            # --- string ---
            if c == '"':
                start = i
                i += 1
                while i < n and code[i] != '"':
                    if code[i] == '\\' and i + 1 < n:
                        i += 2
                    else:
                        i += 1
                i += 1
                yield (start, "Token.Literal.String", code[start:i])
                continue
    
            # --- char literal ---
            if c == "'":
                start = i
                i += 1
                while i < n and code[i] != "'":
                    if code[i] == '\\' and i + 1 < n:
                        i += 2
                    else:
                        i += 1
                i += 1
                yield (start, "Token.Literal.String", code[start:i])
                continue
    
            # --- number ---
            if c.isdigit():
                start = i
                while i < n and (code[i].isdigit() or code[i] in ".eE+-"):
                    i += 1
                yield (start, "Token.Literal.Number", code[start:i])
                continue
    
            # --- identifier / keyword ---
            if c.isalpha() or c == '_':
                start = i
                while i < n and (code[i].isalnum() or code[i] == '_'):
                    i += 1
                val = code[start:i]
                yield (start, "Token.Keyword" if val in KEYWORDS else "Token.Name", val)
                continue
    
            # --- operator ---
            if c in OPERATORS:
                start = i
                op = c
                if i + 1 < n:
                    pair = c + code[i+1]
                    if pair in ("==","!=","<=",">=","->","++","--","&&","||"):
                        op = pair
                        i += 1
                i += 1
                yield (start, "Token.Operator", op)
                continue
    
            # --- punctuation ---
            if c in PUNCT:
                yield (i, "Token.Operator", c)
                i += 1
                continue
    
            # --- unknown ---
            yield (i, "Token.Error", c)
            i += 1

