import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cachoeira import run_source, CachoeiraSyntaxError, CachoeiraRuntimeError


def run(source):
    out = []
    run_source(source, out=out.append)
    return out


class TestCachoeira(unittest.TestCase):
    def test_var_e_print(self):
        out = run('MEMO x = 10\nÉ LOKO, CACHOEIRA! x')
        self.assertEqual(out, ["10"])

    def test_aritmetica(self):
        out = run('É LOKO, CACHOEIRA! 2 + 3 * 4')
        self.assertEqual(out, ["14"])

    def test_if_true(self):
        out = run(
            "SE É LOUCO CACHOEIRA (1 < 2)\n"
            '    É LOKO, CACHOEIRA! "sim"\n'
            "SÓ TRABALHADOR SÓ ZÉ POVINHO\n"
            '    É LOKO, CACHOEIRA! "nao"\n'
            "MEMO, CACHOEIRA, MEMO\n"
        )
        self.assertEqual(out, ["sim"])

    def test_if_false_usa_else(self):
        out = run(
            "SE É LOUCO CACHOEIRA (1 > 2)\n"
            '    É LOKO, CACHOEIRA! "sim"\n'
            "SÓ TRABALHADOR SÓ ZÉ POVINHO\n"
            '    É LOKO, CACHOEIRA! "nao"\n'
            "MEMO, CACHOEIRA, MEMO\n"
        )
        self.assertEqual(out, ["nao"])

    def test_while(self):
        out = run(
            "MEMO i = 0\n"
            "SÓ POR DEUS IRMÃO (i < 3)\n"
            "    É LOKO, CACHOEIRA! i\n"
            "    i = i + 1\n"
            "MEMO, CACHOEIRA, MEMO\n"
        )
        self.assertEqual(out, ["0", "1", "2"])

    def test_try_catch_divisao_por_zero(self):
        out = run(
            "SÓ POR DEUS IRMÃO TENTANDO\n"
            "    É LOKO, CACHOEIRA! 1 / 0\n"
            "EU NÃO ASSUMO ESSE B.O\n"
            '    É LOKO, CACHOEIRA! "capturado"\n'
            "MEMO, CACHOEIRA, MEMO\n"
        )
        self.assertEqual(out, ["capturado"])

    def test_funcao_e_return(self):
        out = run(
            "SOU DE SÃO PAULO FI, NÓIS ROUBA DE PISTOLA dobro(n)\n"
            "    NÃO SOU NEM ENVOLVIDO NO CRIME n * 2\n"
            "MEMO, CACHOEIRA, MEMO\n"
            "É LOKO, CACHOEIRA! dobro(21)\n"
        )
        self.assertEqual(out, ["42"])

    def test_booleanos(self):
        out = run("É LOKO, CACHOEIRA! FI\nÉ LOKO, CACHOEIRA! NUNCA NA VIDA")
        self.assertEqual(out, ["FI", "NUNCA NA VIDA"])

    def test_erro_variavel_inexistente(self):
        with self.assertRaises(CachoeiraRuntimeError):
            run("É LOKO, CACHOEIRA! naoexiste")

    def test_erro_sintaxe(self):
        with self.assertRaises(CachoeiraSyntaxError):
            run("MEMO x 10")


if __name__ == "__main__":
    unittest.main()
