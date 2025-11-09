from vy.filetypes.textfile import TextFile
from vy.filetypes import _register_extension

@_register_extension('.html', '.htm', '.xml')
class HtmlFile(TextFile):
    set_wrap = True
    set_autoindent = True
    set_expandtabs = True
    set_number = True
    set_comment_string = ('<!--', '-->')
    
    def lexer(self, code):
        i, n = 0, len(code)

        def peek(k=0):
            return code[i + k] if i + k < n else ''

        while i < n:
            c = code[i]

            # --- Espaces / lignes vides ---
            if c in ' \t\r\n':
                start = i
                while i < n and code[i] in ' \t\r\n':
                    i += 1
                yield (start, 'Token.Empty', code[start:i])
                continue

            # --- Commentaire HTML <!-- ... --> ---
            if code.startswith('<!--', i):
                start = i
                i += 4
                while i < n - 2 and not code.startswith('-->', i):
                    i += 1
                if i < n:
                    i += 3
                yield (start, 'Token.Comment', code[start:i])
                continue

            # --- DOCTYPE ---
            if code.startswith('<!DOCTYPE', i) or code.startswith('<!doctype', i):
                start = i
                i += 9
                while i < n and code[i] != '>':
                    i += 1
                if i < n:
                    i += 1
                yield (start, 'Token.Title', code[start:i])
                continue

            # --- CDATA ---
            if code.startswith('<![CDATA[', i):
                start = i
                i += 9
                while i < n - 2 and not code.startswith(']]>', i):
                    i += 1
                if i < n:
                    i += 3
                yield (start, 'Token.Literal.String', code[start:i])
                continue

            # --- XML processing instruction ---
            if code.startswith('<?', i):
                start = i
                i += 2
                while i < n - 1 and not code.startswith('?>', i):
                    i += 1
                if i < n:
                    i += 2
                yield (start, 'Token.Subtitle', code[start:i])
                continue

            # --- Début de balise <tag ...> ou </tag> ---
            if c == '<':
                start = i
                i += 1
                if peek() == '/':
                    i += 1
                    kind = 'closing'
                else:
                    kind = 'opening'

                # Nom de la balise
                tag_start = i
                while i < n and (code[i].isalnum() or code[i] in '-_:'):
                    i += 1
                tag_name = code[tag_start:i]

                yield (start, 'Token.Keyword', '<' + ('/' if kind == 'closing' else '') + tag_name)

                # --- Attributs ---
                while i < n:
                    # fin de balise ?
                    if code[i] == '>':
                        yield (i, 'Token.Operator', '>')
                        i += 1
                        break
                    if code[i] == '/':
                        if peek(1) == '>':
                            yield (i, 'Token.Operator', '/>')
                            i += 2
                            break

                    # espaces
                    if code[i] in ' \t\r\n':
                        s = i
                        while i < n and code[i] in ' \t\r\n':
                            i += 1
                        yield (s, 'Token.Empty', code[s:i])
                        continue

                    # nom d'attribut
                    attr_start = i
                    while i < n and (code[i].isalnum() or code[i] in '-_:'):
                        i += 1
                    attr_name = code[attr_start:i]
                    if attr_name:
                        yield (attr_start, 'Token.Name.Builtin', attr_name)

                    # opérateur =
                    if i < n and code[i] == '=':
                        yield (i, 'Token.Operator', '=')
                        i += 1

                        # valeur entre guillemets
                        if i < n and code[i] in ('"', "'"):
                            q = code[i]
                            val_start = i
                            i += 1
                            while i < n and code[i] != q:
                                i += 1
                            if i < n:
                                i += 1
                            yield (val_start, 'Token.Literal.String', code[val_start:i])
                    continue
                continue

            # --- Texte brut entre balises ---
            start = i
            while i < n and code[i] != '<':
                i += 1
            text = code[start:i]
            if text.strip() != '':
                yield (start, 'Token.Statement', text)
            else:
                yield (start, 'Token.Empty', text)

        # --- EOF ---
        yield (n, 'Token.Empty', '')
