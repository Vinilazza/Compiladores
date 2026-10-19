from .lexer import tokenize
from .parser import parse
from .interpreter import Interpreter
from .codegen import TARGETS, translate
from .errors import CachoeiraSyntaxError, CachoeiraRuntimeError

__all__ = [
    "tokenize",
    "parse",
    "Interpreter",
    "TARGETS",
    "translate",
    "traduzir",
    "CachoeiraSyntaxError",
    "CachoeiraRuntimeError",
]


def run_source(source: str, out=print):
    tokens = tokenize(source)
    program = parse(tokens)
    Interpreter(out=out).run(program)


def traduzir(source: str, alvo: str) -> str:
    """Traduz código CACHOEIRA pra outra linguagem (python, javascript, lua, ruby)."""
    return translate(parse(tokenize(source)), alvo)
