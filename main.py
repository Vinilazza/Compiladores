#!/usr/bin/env python3
"""CLI da linguagem CACHOEIRA: python main.py caminho/pro/arquivo.cch"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cachoeira import TARGETS, traduzir, run_source, CachoeiraSyntaxError, CachoeiraRuntimeError


def main():
    parser = argparse.ArgumentParser(description="Interpretador/tradutor da linguagem CACHOEIRA")
    parser.add_argument("arquivo", help="arquivo .cch")
    parser.add_argument(
        "--para", metavar="LINGUAGEM", choices=sorted(TARGETS),
        help="em vez de executar, traduz o programa (" + ", ".join(sorted(TARGETS)) + ")",
    )
    parser.add_argument("-o", "--saida", help="grava a tradução neste arquivo (padrão: stdout)")
    args = parser.parse_args()

    path = Path(args.arquivo)
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[erro] não consegui abrir '{path}': {exc.strerror}")
        sys.exit(1)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        if args.para:
            code = traduzir(source, args.para)
            if args.saida:
                Path(args.saida).write_text(code, encoding="utf-8")
            else:
                print(code, end="")
        else:
            run_source(source)
    except CachoeiraSyntaxError as exc:
        print(f"[erro de sintaxe] {exc}")
        sys.exit(1)
    except CachoeiraRuntimeError as exc:
        print(f"[erro em tempo de execução] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
