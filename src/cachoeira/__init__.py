from .lexer import tokenize
from .parser import parse
from .interpreter import Interpreter
from .errors import CachoeiraSyntaxError, CachoeiraRuntimeError

__all__ = [
    "tokenize",
    "parse",
    "Interpreter",
    "CachoeiraSyntaxError",
    "CachoeiraRuntimeError",
]


def run_source(source: str, out=print):
    tokens = tokenize(source)
    program = parse(tokens)
    Interpreter(out=out).run(program)
