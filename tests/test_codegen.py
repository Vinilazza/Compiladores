"""Garante que o código traduzido produz a mesma saída que o interpretador."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cachoeira import run_source, traduzir, CachoeiraSyntaxError

PROGRAMAS = {
    'escopo_funcao': 'MEMO total = 0\nSOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA soma(n)\n    MEMO i = 0\n    SÓ POR DEUS IRMÃO (i < n)\n        total = total + i\n        i = i + 1\n    MEMO, CACHOEIRA, MEMO\nMEMO, CACHOEIRA, MEMO\nsoma(5)\nÉ LOKO, CACHOEIRA! total\n',
    'aninhada_closure': 'SOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA contador()\n    MEMO c = 0\n    SOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA inc()\n        c = c + 1\n        NÃO SOU NEM ENVOLVIDO NO CRIME c\n    MEMO, CACHOEIRA, MEMO\n    inc()\n    inc()\n    NÃO SOU NEM ENVOLVIDO NO CRIME inc()\nMEMO, CACHOEIRA, MEMO\nÉ LOKO, CACHOEIRA! contador()\n',
    'try_return': 'SOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA f(x)\n    SÓ POR DEUS IRMÃO TENTANDO\n        SE É LOUCO CACHOEIRA (x == 0)\n            NÃO SOU NEM ENVOLVIDO NO CRIME 1 / x\n        MEMO, CACHOEIRA, MEMO\n        NÃO SOU NEM ENVOLVIDO NO CRIME "ok"\n    EU NÃO ASSUMO ESSE B.O\n        NÃO SOU NEM ENVOLVIDO NO CRIME "capturado"\n    MEMO, CACHOEIRA, MEMO\n    NÃO SOU NEM ENVOLVIDO NO CRIME "nunca"\nMEMO, CACHOEIRA, MEMO\nÉ LOKO, CACHOEIRA! f(0)\nÉ LOKO, CACHOEIRA! f(2)\n',
    'tipos': 'É LOKO, CACHOEIRA! 10 / 4\nÉ LOKO, CACHOEIRA! 10 / 5\nÉ LOKO, CACHOEIRA! "a" + 1 + FI\nÉ LOKO, CACHOEIRA! !0\nÉ LOKO, CACHOEIRA! 0 || ""\nÉ LOKO, CACHOEIRA! 1 && "x"\nÉ LOKO, CACHOEIRA! !(1 < 2)\nÉ LOKO, CACHOEIRA! TAMANHO("cachoeira")\nÉ LOKO, CACHOEIRA! "tab\\taspas \\" barra \\\\ $x #{y}"\nÉ LOKO, CACHOEIRA! -3 + 5\nÉ LOKO, CACHOEIRA! 1 != 2\nSOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA nada()\nMEMO, CACHOEIRA, MEMO\nÉ LOKO, CACHOEIRA! nada()\n',
    'nomes': 'MEMO Número = 3\nMEMO class = 4\nMEMO end = 5\nMEMO print = 6\nMEMO cch_x = 7\nÉ LOKO, CACHOEIRA! Número + class + end + print + cch_x\n',
    'zero_capturado': 'SÓ POR DEUS IRMÃO TENTANDO\n    É LOKO, CACHOEIRA! 1 / 0\nEU NÃO ASSUMO ESSE B.O\n    É LOKO, CACHOEIRA! "pego"\nMEMO, CACHOEIRA, MEMO\n',
    'vazio': 'SE É LOUCO CACHOEIRA (NUNCA NA VIDA)\nMEMO, CACHOEIRA, MEMO\nSÓ POR DEUS IRMÃO TENTANDO\nEU NÃO ASSUMO ESSE B.O\nMEMO, CACHOEIRA, MEMO\nSOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA g()\nMEMO, CACHOEIRA, MEMO\nÉ LOKO, CACHOEIRA! "fim"\n',
}
for _f in sorted((Path(__file__).parent.parent / "examples").glob("*.cch")):
    PROGRAMAS[_f.name] = _f.read_text(encoding="utf-8")

COMANDOS = {
    "python": [sys.executable],
    "javascript": [shutil.which("node")],
    "ruby": [shutil.which("ruby")],
    "lua": [shutil.which("lua") or shutil.which("lua5.4") or shutil.which("luajit")],
}
EXTENSOES = {"python": ".py", "javascript": ".js", "ruby": ".rb", "lua": ".lua"}


def esperado(source):
    out = []
    run_source(source, out=out.append)
    return "\n".join(out)


class TestTradutor(unittest.TestCase):
    def test_alvo_desconhecido(self):
        with self.assertRaises(ValueError):
            traduzir("É LOKO, CACHOEIRA! 1", "cobol")

    def test_return_fora_de_funcao(self):
        with self.assertRaises(CachoeiraSyntaxError):
            traduzir("NÃO SOU NEM ENVOLVIDO NO CRIME 1", "python")

    def test_alias(self):
        self.assertEqual(traduzir("É LOKO, CACHOEIRA! 1", "js"), traduzir("É LOKO, CACHOEIRA! 1", "javascript"))


class TestSiteSincronizado(unittest.TestCase):
    def test_docs_tem_copia_atual_do_codigo(self):
        raiz = Path(__file__).parent.parent
        for arq in (raiz / "src" / "cachoeira").glob("*.py"):
            copia = raiz / "docs" / "cachoeira" / arq.name
            self.assertTrue(copia.exists() and copia.read_bytes() == arq.read_bytes(),
                            f"docs/cachoeira/{arq.name} desatualizado — rode scripts/build_site.sh")
        for arq in (raiz / "examples").glob("*.cch"):
            copia = raiz / "docs" / "examples" / arq.name
            self.assertTrue(copia.exists() and copia.read_bytes() == arq.read_bytes(),
                            f"docs/examples/{arq.name} desatualizado — rode scripts/build_site.sh")


def _criar_teste(alvo):
    def teste(self):
        cmd = COMANDOS[alvo]
        if cmd[0] is None:
            self.skipTest(f"{alvo} não instalado")
        for nome, source in PROGRAMAS.items():
            with self.subTest(programa=nome):
                with tempfile.TemporaryDirectory() as tmp:
                    arq = Path(tmp) / ("prog" + EXTENSOES[alvo])
                    arq.write_text(traduzir(source, alvo), encoding="utf-8")
                    r = subprocess.run(cmd + [str(arq)], capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.strip(), esperado(source))
    return teste


for _alvo in COMANDOS:
    setattr(TestTradutor, f"test_traducao_{_alvo}_equivale_ao_interpretador", _criar_teste(_alvo))


if __name__ == "__main__":
    unittest.main()
