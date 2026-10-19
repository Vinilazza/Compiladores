#!/usr/bin/env bash
# Sincroniza docs/ (a pasta publicada pelo GitHub Pages) com o código da linguagem:
# o playground carrega docs/cachoeira/*.py e docs/examples/* no navegador (Pyodide).
# Rode depois de mexer em src/ ou examples/ e commite o resultado.
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf docs/cachoeira docs/examples
mkdir -p docs/cachoeira docs/examples
cp src/cachoeira/*.py docs/cachoeira/
cp examples/*.cch docs/examples/
ls examples/*.cch | xargs -n1 basename | python3 -c \
  'import sys, json; print(json.dumps(sorted(l.strip() for l in sys.stdin)))' > docs/examples/index.json
touch docs/.nojekyll
echo "docs/ sincronizado"
