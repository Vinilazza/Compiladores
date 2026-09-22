class CachoeiraSyntaxError(Exception):
    """Erro léxico ou sintático (o BO é do programador)."""


class CachoeiraRuntimeError(Exception):
    """Erro em tempo de execução (capturável por EU NÃO ASSUMO ESSE B.O)."""
