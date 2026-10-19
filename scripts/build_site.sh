#!/usr/bin/env bash
# Monta o site estático em _site/: landing page (docs/) + código da linguagem
# (usado pelo playground rodando Python no navegador via Pyodide) + exemplos.
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf _site
mkdir -p _site/cachoeira _site/examples
cp docs/index.html _site/
cp src/cachoeira/*.py _site/cachoeira/
cp examples/*.cch _site/examples/
ls examples/*.cch | xargs -n1 basename | python3 -c \
  'import sys, json; print(json.dumps(sorted(l.strip() for l in sys.stdin)))' > _site/examples/index.json
echo "site pronto em _site/"
