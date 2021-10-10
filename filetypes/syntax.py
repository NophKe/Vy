try:
    from .pygments_lexer import view
except ImportError:
    from .simple_lexer import view


