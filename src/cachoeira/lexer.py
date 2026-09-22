"""
Analisador léxico da linguagem CACHOEIRA.

As palavras-chave são bordões do vídeo viral do "Cachoeira" (assalto/facada
no mercado). O léxico casa os bordões primeiro (do mais longo pro mais
curto, pra não confundir "MEMO, CACHOEIRA, MEMO" com "MEMO" sozinho) e
depois cai pros tokens genéricos (identificador, número, string, símbolo).
"""
import re
from collections import namedtuple

from .errors import CachoeiraSyntaxError

Token = namedtuple("Token", ["type", "value", "line"])

# Ordem importa: padrões mais específicos/longos primeiro.
KEYWORD_PATTERNS = [
    # MEMO, CACHOEIRA, MEMO  -> fecha qualquer bloco (if/else/while/try/função)
    ("END", r"MEMO\s*,?\s*CACHOEIRA\s*,?\s*MEMO"),
    # É LOKO, CACHOEIRA!  -> print
    ("PRINT", r"[EÉ]\s*LOKO\s*,?\s*CACHOEIRA\s*!?"),
    # SOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA  -> definição de função
    ("FUNC", r"SOU\s+DE\s+S[AÃ]O\s+PAULO\s+FI\s*,?\s+N[OÓ]IS\s+ROUBA\s+DE\s+PISTOLA"),
    # NÃO SOU NEM ENVOLVIDO NO CRIME  -> return
    ("RETURN", r"N[AÃ]O\s+SOU\s+NEM\s+ENVOLVIDO\s+NO\s+CRIME"),
    # SE É LOUCO CACHOEIRA  -> if
    ("IF", r"SE\s+[EÉ]\s+LOUCO\s+CACHOEIRA"),
    # SÓ TRABALHADOR SÓ ZÉ POVINHO  -> else
    ("ELSE", r"S[OÓ]\s+TRABALHADOR\s+S[OÓ]\s+Z[EÉ]\s+POVINHO"),
    # SÓ POR DEUS IRMÃO  -> while, ou (seguido de TENTANDO) início de try
    ("WHILE_OR_TRY", r"S[OÓ]\s+POR\s+DEUS\s+IRM[AÃ]O"),
    ("TENTANDO", r"TENTANDO\b"),
    # EU NÃO ASSUMO ESSE B.O  -> catch
    ("CATCH", r"EU\s+N[AÃ]O\s+ASSUMO\s+ESSE\s+B\.?\s*O\.?"),
    # NUNCA NA VIDA  -> literal falso
    ("FALSE", r"NUNCA\s+NA\s+VIDA\b"),
    # FI  -> literal verdadeiro ("sou de são paulo FI")
    ("TRUE", r"FI\b"),
    # MEMO  -> declaração de variável ("bora memorizar")
    ("VAR", r"MEMO\b"),
]

SYMBOLS = [
    ("EQEQ", r"=="),
    ("NEQ", r"!="),
    ("LE", r"<="),
    ("GE", r">="),
    ("AND", r"&&"),
    ("OR", r"\|\|"),
    ("EQ", r"="),
    ("LT", r"<"),
    ("GT", r">"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("STAR", r"\*"),
    ("SLASH", r"/"),
    ("BANG", r"!"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMMA", r","),
]

NUMBER_RE = re.compile(r"\d+(\.\d+)?")
STRING_RE = re.compile(r'"([^"\\]|\\.)*"')
IDENT_RE = re.compile(r"[A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]*")
NEWLINE_RE = re.compile(r"\n")
WHITESPACE_RE = re.compile(r"[ \t\r]+")
COMMENT_RE = re.compile(r"#[^\n]*")

_COMPILED_KEYWORDS = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in KEYWORD_PATTERNS]
_COMPILED_SYMBOLS = [(name, re.compile(pat)) for name, pat in SYMBOLS]


_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _decode_string_escapes(raw: str) -> str:
    out = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\\" and i + 1 < len(raw):
            out.append(_ESCAPES.get(raw[i + 1], raw[i + 1]))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def tokenize(source: str):
    tokens = []
    pos = 0
    line = 1
    n = len(source)

    while pos < n:
        m = NEWLINE_RE.match(source, pos)
        if m:
            line += 1
            pos = m.end()
            continue

        m = WHITESPACE_RE.match(source, pos)
        if m:
            pos = m.end()
            continue

        m = COMMENT_RE.match(source, pos)
        if m:
            pos = m.end()
            continue

        matched = False

        for name, regex in _COMPILED_KEYWORDS:
            m = regex.match(source, pos)
            if m:
                tokens.append(Token(name, m.group(0), line))
                pos = m.end()
                matched = True
                break
        if matched:
            continue

        m = STRING_RE.match(source, pos)
        if m:
            raw = m.group(0)[1:-1]
            value = _decode_string_escapes(raw)
            tokens.append(Token("STRING", value, line))
            pos = m.end()
            continue

        m = NUMBER_RE.match(source, pos)
        if m:
            text = m.group(0)
            value = float(text) if "." in text else int(text)
            tokens.append(Token("NUMBER", value, line))
            pos = m.end()
            continue

        for name, regex in _COMPILED_SYMBOLS:
            m = regex.match(source, pos)
            if m:
                tokens.append(Token(name, m.group(0), line))
                pos = m.end()
                matched = True
                break
        if matched:
            continue

        m = IDENT_RE.match(source, pos)
        if m:
            tokens.append(Token("IDENT", m.group(0), line))
            pos = m.end()
            continue

        raise CachoeiraSyntaxError(
            f"Linha {line}: caractere inesperado {source[pos]!r} — só por deus irmão, arruma essa sintaxe"
        )

    tokens.append(Token("EOF", None, line))
    return tokens
