#!/usr/bin/env python3
"""CLI da linguagem CACHOEIRA: python main.py caminho/pro/arquivo.cch"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cachoeira import run_source, CachoeiraSyntaxError, CachoeiraRuntimeError


def main():
    if len(sys.argv) != 2:
        print("uso: python main.py <arquivo.cch>")
        sys.exit(1)

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")

    try:
        run_source(source)
    except CachoeiraSyntaxError as exc:
        print(f"[erro de sintaxe] {exc}")
        sys.exit(1)
    except CachoeiraRuntimeError as exc:
        print(f"[erro em tempo de execução] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
