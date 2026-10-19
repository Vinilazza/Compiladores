"""
Tradutor CACHOEIRA -> outras linguagens (Python, JavaScript, Lua, Ruby).

Percorre a mesma AST que o interpretador usa e gera código-fonte equivalente.
Todos os alvos são dinamicamente tipados, igual à CACHOEIRA; linguagens
estáticas (C, Java, Go) exigiriam inferência de tipos e ficam de fora.

Cada saída começa com um pequeno "prelúdio" (funções cch_*) que reproduz as
regras da CACHOEIRA: FI / NUNCA NA VIDA ao imprimir, `+` que concatena texto,
divisão por zero como erro e truthiness (0 e "" são falsos).
"""
import re
import unicodedata

from . import ast_nodes as ast
from .errors import CachoeiraSyntaxError

COMPARISONS = {"<", ">", "<=", ">=", "==", "!="}


def _is_bool(node):
    if isinstance(node, ast.Literal):
        return isinstance(node.value, bool)
    if isinstance(node, ast.UnaryOp):
        return node.op == "!"
    if isinstance(node, ast.BinOp):
        return node.op in COMPARISONS or node.op in ("&&", "||")
    return False


def _is_numeric(node):
    if isinstance(node, ast.Literal):
        return isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
    if isinstance(node, ast.UnaryOp):
        return node.op == "-"
    if isinstance(node, ast.BinOp):
        return node.op in ("-", "*", "/")
    return False


def _unparen(code):
    """Tira os parênteses externos de `(a + b)` quando eles envolvem tudo."""
    if not (code.startswith("(") and code.endswith(")")):
        return code
    depth = 0
    in_str = None
    i = 0
    while i < len(code):
        ch = code[i]
        if in_str:
            if ch == "\\":
                i += 1
            elif ch == in_str:
                in_str = None
        elif ch in "\"'":
            in_str = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and i != len(code) - 1:
                return code
        i += 1
    return code[1:-1]


def _walk_scope(stmts, declared, assigned):
    """Coleta nomes declarados/atribuídos num corpo de função (sem entrar em funções aninhadas)."""
    for s in stmts:
        if isinstance(s, ast.VarDecl):
            declared.add(s.name)
        elif isinstance(s, ast.FuncDef):
            declared.add(s.name)
        elif isinstance(s, ast.Assign):
            assigned.add(s.name)
        elif isinstance(s, ast.If):
            _walk_scope(s.then_body, declared, assigned)
            _walk_scope(s.else_body, declared, assigned)
        elif isinstance(s, ast.While):
            _walk_scope(s.body, declared, assigned)
        elif isinstance(s, ast.Try):
            _walk_scope(s.try_body, declared, assigned)
            _walk_scope(s.catch_body, declared, assigned)


class Generator:
    label = ""
    indent_unit = "  "
    reserved = frozenset()
    true, false, nil = "true", "false", "nil"

    def __init__(self):
        self.out = []
        self.level = 0
        self.fn_depth = 0
        self.names = {}

    # ---------- infra ----------
    def line(self, text=""):
        self.out.append(self.indent_unit * self.level + text if text else "")

    def generate(self, program):
        self.out = []
        self.prelude()
        self.stmts(program.statements)
        return "\n".join(self.out) + "\n"

    def stmts(self, statements):
        for s in statements:
            getattr(self, "s_" + type(s).__name__)(s)

    def body(self, statements, before=None):
        """Emite um bloco indentado; `before` roda já dentro da indentação."""
        self.level += 1
        start = len(self.out)
        if before:
            before()
        self.stmts(statements)
        if len(self.out) == start:
            self.empty_block()
        self.level -= 1

    def empty_block(self):
        pass

    def ident(self, name):
        if name in self.names:
            return self.names[name]
        out = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
        out = re.sub(r"\W", "", out) or "v"
        if out[0].isdigit():
            out = "_" + out
        if out in self.reserved or out.startswith("cch_"):
            out += "_"
        out = self.fix_ident(out)
        self.names[name] = out
        return out

    def fix_ident(self, name):
        return name

    def string(self, value):
        out = ['"']
        for ch in value:
            out.append(self.escape_char(ch))
        out.append('"')
        return "".join(out)

    def escape_char(self, ch):
        return {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\t": "\\t", "\r": "\\r"}.get(ch, ch)

    def check_return(self, stmt):
        if self.fn_depth == 0:
            raise CachoeiraSyntaxError(
                f"Linha {stmt.line}: 'NÃO SOU NEM ENVOLVIDO NO CRIME' fora de uma função não dá pra traduzir"
            )

    # ---------- expressões ----------
    def expr(self, n):
        if isinstance(n, ast.Literal):
            v = n.value
            if v is True:
                return self.true
            if v is False:
                return self.false
            if v is None:
                return self.nil
            if isinstance(v, str):
                return self.string(v)
            return repr(v)
        if isinstance(n, ast.Var):
            return self.ident(n.name)
        if isinstance(n, ast.UnaryOp):
            inner = self.expr(n.expr)
            return f"(-{inner})" if n.op == "-" else self.not_(inner, _is_bool(n.expr))
        if isinstance(n, ast.BinOp):
            return self.binop(n)
        if isinstance(n, ast.Call):
            args = [self.expr(a) for a in n.args]
            if n.name == "TAMANHO":
                if len(args) != 1:
                    raise CachoeiraSyntaxError(f"Linha {n.line}: TAMANHO espera 1 argumento")
                return self.length(args[0])
            return self.call(self.ident(n.name), args)
        raise CachoeiraSyntaxError(f"nó de expressão desconhecido: {type(n).__name__}")

    def binop(self, n):
        op = n.op
        left, right = self.expr(n.left), self.expr(n.right)
        if op in ("&&", "||"):
            lb, rb = _is_bool(n.left), _is_bool(n.right)
            return self.logic(op, left, right, lb, rb)
        if op == "+":
            if _is_numeric(n.left) and _is_numeric(n.right):
                return f"({left} + {right})"
            return f"cch_soma({left}, {right})"
        if op == "/":
            return f"cch_div({left}, {right})"
        if op == "==":
            return f"({left} {self.eq} {right})"
        if op == "!=":
            return f"({left} {self.ne} {right})"
        return f"({left} {op} {right})"

    eq, ne = "==", "!="

    def call(self, name, args):
        return f"{name}({', '.join(args)})"

    def cond(self, node):
        return _unparen(self.expr(node))


# ======================================================================
class PythonGen(Generator):
    label = "Python"
    indent_unit = "    "
    true, false, nil = "True", "False", "None"
    reserved = frozenset(
        "False None True and as assert async await break class continue def del elif else except "
        "finally for from global if import in is lambda nonlocal not or pass raise return try while "
        "with yield print len bool str int float isinstance Exception ZeroDivisionError".split()
    )

    PRELUDE = '''def cch_mostrar(v):
    if v is True:
        return "FI"
    if v is False or v is None:
        return "NUNCA NA VIDA"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def cch_soma(a, b):
    if isinstance(a, str) or isinstance(b, str):
        return cch_mostrar(a) + cch_mostrar(b)
    return a + b


def cch_div(a, b):
    if b == 0:
        raise ZeroDivisionError("divisão por zero")
    return a / b

'''

    def __init__(self):
        super().__init__()
        self.fn_declared = []  # pilha de conjuntos de nomes locais por função

    def prelude(self):
        self.out.extend(self.PRELUDE.rstrip("\n").split("\n"))
        self.line()
        self.line()

    def empty_block(self):
        self.line("pass")

    def not_(self, inner, is_bool=False):
        return f"(not {inner})"

    def logic(self, op, l, r, lb, rb):
        word = "and" if op == "&&" else "or"
        l = l if lb else f"bool({l})"
        r = r if rb else f"bool({r})"
        return f"({l} {word} {r})"

    def length(self, arg):
        return f"len({arg})"

    def s_VarDecl(self, s):
        self.line(f"{self.ident(s.name)} = {self.cond(s.expr)}")

    s_Assign = s_VarDecl

    def s_Print(self, s):
        self.line(f"print(cch_mostrar({self.cond(s.expr)}))")

    def s_ExprStmt(self, s):
        self.line(self.cond(s.expr))

    def s_If(self, s):
        self.line(f"if {self.cond(s.cond)}:")
        self.body(s.then_body)
        if s.else_body:
            self.line("else:")
            self.body(s.else_body)

    def s_While(self, s):
        self.line(f"while {self.cond(s.cond)}:")
        self.body(s.body)

    def s_Try(self, s):
        self.line("try:")
        self.body(s.try_body)
        self.line("except Exception:")
        self.body(s.catch_body)

    def s_FuncDef(self, s):
        declared, assigned = set(s.params), set()
        _walk_scope(s.body, declared, assigned)
        outer = [name for name in assigned if name not in declared]
        nonlocals, globals_ = [], []
        for name in sorted(outer):
            if any(name in scope for scope in self.fn_declared):
                nonlocals.append(self.ident(name))
            else:
                globals_.append(self.ident(name))

        def decls():
            if nonlocals:
                self.line("nonlocal " + ", ".join(nonlocals))
            if globals_:
                self.line("global " + ", ".join(globals_))

        params = ", ".join(self.ident(p) for p in s.params)
        self.line(f"def {self.ident(s.name)}({params}):")
        self.fn_declared.append(declared)
        self.fn_depth += 1
        self.body(s.body, before=decls)
        self.fn_depth -= 1
        self.fn_declared.pop()

    def s_Return(self, s):
        self.check_return(s)
        self.line("return " + (self.cond(s.expr) if s.expr is not None else "None"))


# ======================================================================
class JavaScriptGen(Generator):
    label = "JavaScript"
    reserved = frozenset(
        "break case catch class const continue debugger default delete do else enum export extends "
        "false finally for function if import in instanceof new null return super switch this throw "
        "true try typeof var void while with yield let static implements interface package private "
        "protected public await async undefined NaN Infinity console String Error".split()
    )
    eq, ne = "===", "!=="

    PRELUDE = '''function cch_mostrar(v) {
  if (v === true) return "FI";
  if (v === false || v === null || v === undefined) return "NUNCA NA VIDA";
  return String(v);
}

function cch_soma(a, b) {
  if (typeof a === "string" || typeof b === "string") return cch_mostrar(a) + cch_mostrar(b);
  return a + b;
}

function cch_div(a, b) {
  if (b === 0) throw new Error("divisão por zero");
  return a / b;
}
'''

    def __init__(self):
        super().__init__()
        self.scopes = [set()]

    def prelude(self):
        self.out.extend(self.PRELUDE.rstrip("\n").split("\n"))
        self.line()

    def not_(self, inner, is_bool=False):
        return f"(!{inner})"

    def logic(self, op, l, r, lb, rb):
        l = l if lb else f"!!{l}"
        r = r if rb else f"!!{r}"
        return f"({l} {op} {r})"

    def length(self, arg):
        return f"({arg}).length"

    def scoped_body(self, statements, names=()):
        self.scopes.append(set(names))
        self.body(statements)
        self.scopes.pop()

    def decl_head(self, name):
        ident = self.ident(name)
        if name in self.scopes[-1]:
            return ident
        self.scopes[-1].add(name)
        return "let " + ident

    def s_VarDecl(self, s):
        self.line(f"{self.decl_head(s.name)} = {self.cond(s.expr)};")

    def s_Assign(self, s):
        self.line(f"{self.ident(s.name)} = {self.cond(s.expr)};")

    def s_Print(self, s):
        self.line(f"console.log(cch_mostrar({self.cond(s.expr)}));")

    def s_ExprStmt(self, s):
        self.line(self.cond(s.expr) + ";")

    def s_If(self, s):
        self.line(f"if ({self.cond(s.cond)}) {{")
        self.scoped_body(s.then_body)
        if s.else_body:
            self.line("} else {")
            self.scoped_body(s.else_body)
        self.line("}")

    def s_While(self, s):
        self.line(f"while ({self.cond(s.cond)}) {{")
        self.scoped_body(s.body)
        self.line("}")

    def s_Try(self, s):
        self.line("try {")
        self.scoped_body(s.try_body)
        self.line("} catch (_erro) {")
        self.scoped_body(s.catch_body)
        self.line("}")

    def s_FuncDef(self, s):
        head = self.decl_head(s.name)
        params = ", ".join(self.ident(p) for p in s.params)
        self.line(f"{head} = function ({params}) {{")
        self.fn_depth += 1
        self.scoped_body(s.body, names=s.params)
        self.fn_depth -= 1
        self.line("};")

    def s_Return(self, s):
        self.check_return(s)
        self.line("return" + (" " + self.cond(s.expr) if s.expr is not None else "") + ";")


# ======================================================================
class LuaGen(Generator):
    label = "Lua"
    reserved = frozenset(
        "and break do else elseif end false for function goto if in local nil not or repeat return "
        "then true until while print tostring type string math pcall error".split()
    )
    eq, ne = "==", "~="

    PRELUDE = '''local function cch_mostrar(v)
  if v == true then return "FI" end
  if v == false or v == nil then return "NUNCA NA VIDA" end
  if type(v) == "number" and v == math.floor(v) and math.abs(v) < 2 ^ 53 then
    return string.format("%d", v)
  end
  return tostring(v)
end

local function cch_v(x)
  return not (x == nil or x == false or x == 0 or x == "")
end

local function cch_soma(a, b)
  if type(a) == "string" or type(b) == "string" then return cch_mostrar(a) .. cch_mostrar(b) end
  return a + b
end

local function cch_div(a, b)
  if b == 0 then error("divisão por zero") end
  return a / b
end
'''

    def __init__(self):
        super().__init__()
        self.try_depth = 0
        self.try_count = 0

    def prelude(self):
        self.out.extend(self.PRELUDE.rstrip("\n").split("\n"))
        self.line()

    def truth(self, code, is_bool):
        return code if is_bool else f"cch_v({code})"

    def not_(self, inner, is_bool=False):
        return f"(not {self.truth(inner, is_bool)})"

    def logic(self, op, l, r, lb, rb):
        word = "and" if op == "&&" else "or"
        return f"({self.truth(l, lb)} {word} {self.truth(r, rb)})"

    def length(self, arg):
        return f"#({arg})"

    def escape_char(self, ch):
        return {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\t": "\\t", "\r": "\\r"}.get(ch, ch)

    def binop(self, n):
        # concatenação e demais operadores seguem o caminho genérico
        return super().binop(n)

    def s_VarDecl(self, s):
        self.line(f"local {self.ident(s.name)} = {self.cond(s.expr)}")

    def s_Assign(self, s):
        self.line(f"{self.ident(s.name)} = {self.cond(s.expr)}")

    def s_Print(self, s):
        self.line(f"print(cch_mostrar({self.cond(s.expr)}))")

    def s_ExprStmt(self, s):
        self.line(f"local _ = {self.cond(s.expr)}")

    def s_If(self, s):
        self.line(f"if {self.truth(self.cond(s.cond), _is_bool(s.cond))} then")
        self.body(s.then_body)
        if s.else_body:
            self.line("else")
            self.body(s.else_body)
        self.line("end")

    def s_While(self, s):
        self.line(f"while {self.truth(self.cond(s.cond), _is_bool(s.cond))} do")
        self.body(s.body)
        self.line("end")

    def return_stmt(self, code):
        # `return` precisa ser o último comando do bloco em Lua; dentro de pcall
        # o valor vai "embalado" numa tabela pra distinguir `return nil` de fim normal.
        if self.try_depth > 0:
            self.line(f"do return {{{code}}} end")
        else:
            self.line(f"do return {code} end")

    def s_Return(self, s):
        self.check_return(s)
        self.return_stmt(self.cond(s.expr) if s.expr is not None else "nil")

    def s_Try(self, s):
        self.try_count += 1
        ok, ret = f"cch_ok{self.try_count}", f"cch_ret{self.try_count}"
        self.line(f"local {ok}, {ret} = pcall(function()")
        self.try_depth += 1
        self.body(s.try_body)
        self.try_depth -= 1
        self.line("end)")
        self.line(f"if {ok} then")
        if self.fn_depth > 0:
            self.level += 1
            self.line(f"if {ret} ~= nil then")
            self.level += 1
            self.return_stmt(f"{ret}[1]")
            self.level -= 1
            self.line("end")
            self.level -= 1
        self.line("else")
        self.body(s.catch_body)
        self.line("end")

    def s_FuncDef(self, s):
        params = ", ".join(self.ident(p) for p in s.params)
        self.line(f"local function {self.ident(s.name)}({params})")
        saved, self.try_depth = self.try_depth, 0
        self.fn_depth += 1
        self.body(s.body)
        self.fn_depth -= 1
        self.try_depth = saved
        self.line("end")


# ======================================================================
class RubyGen(Generator):
    label = "Ruby"
    reserved = frozenset(
        "BEGIN END alias and begin break case class def defined? do else elsif end ensure false for "
        "if in module next nil not or redo rescue retry return self super then true undef unless "
        "until when while yield puts lambda raise".split()
    )

    PRELUDE = '''def cch_mostrar(v)
  return "FI" if v == true
  return "NUNCA NA VIDA" if v == false || v.nil?
  return v.to_i.to_s if v.is_a?(Float) && v.finite? && v == v.floor
  v.to_s
end

def cch_v(x)
  !(x.nil? || x == false || x == 0 || x == "")
end

def cch_soma(a, b)
  return cch_mostrar(a) + cch_mostrar(b) if a.is_a?(String) || b.is_a?(String)
  a + b
end

def cch_div(a, b)
  raise "divisão por zero" if b == 0
  a.fdiv(b)
end
'''

    def prelude(self):
        self.out.extend(self.PRELUDE.rstrip("\n").split("\n"))
        self.line()

    def fix_ident(self, name):
        # em Ruby, começar com maiúscula vira constante (e `def` não enxerga variáveis)
        return "_" + name if name[0].isupper() else name

    def escape_char(self, ch):
        return {
            "\\": "\\\\", '"': '\\"', "\n": "\\n", "\t": "\\t", "\r": "\\r", "#": "\\#",
        }.get(ch, ch)

    def truth(self, code, is_bool):
        return code if is_bool else f"cch_v({code})"

    def not_(self, inner, is_bool=False):
        return f"(!{self.truth(inner, is_bool)})"

    def logic(self, op, l, r, lb, rb):
        return f"({self.truth(l, lb)} {op} {self.truth(r, rb)})"

    def length(self, arg):
        return f"({arg}).length"

    def call(self, name, args):
        return f"{name}.call({', '.join(args)})"

    def s_VarDecl(self, s):
        self.line(f"{self.ident(s.name)} = {self.cond(s.expr)}")

    s_Assign = s_VarDecl

    def s_Print(self, s):
        self.line(f"puts cch_mostrar({self.cond(s.expr)})")

    def s_ExprStmt(self, s):
        self.line(self.cond(s.expr))

    def s_If(self, s):
        self.line(f"if {self.truth(self.cond(s.cond), _is_bool(s.cond))}")
        self.body(s.then_body)
        if s.else_body:
            self.line("else")
            self.body(s.else_body)
        self.line("end")

    def s_While(self, s):
        self.line(f"while {self.truth(self.cond(s.cond), _is_bool(s.cond))}")
        self.body(s.body)
        self.line("end")

    def s_Try(self, s):
        self.line("begin")
        self.body(s.try_body)
        self.line("rescue StandardError, SystemStackError")
        self.body(s.catch_body)
        self.line("end")

    def s_FuncDef(self, s):
        params = ", ".join(self.ident(p) for p in s.params)
        pipes = f" |{params}|" if params else ""
        # lambda (e não `def`) pra enxergar as variáveis de fora, como a CACHOEIRA
        self.line(f"{self.ident(s.name)} = lambda do{pipes}")
        self.fn_depth += 1
        self.level += 1
        self.stmts(s.body)
        self.line("nil")
        self.level -= 1
        self.fn_depth -= 1
        self.line("end")

    def s_Return(self, s):
        self.check_return(s)
        self.line("return " + (self.cond(s.expr) if s.expr is not None else "nil"))


TARGETS = {
    "python": PythonGen,
    "javascript": JavaScriptGen,
    "lua": LuaGen,
    "ruby": RubyGen,
}

ALIASES = {"py": "python", "js": "javascript", "node": "javascript", "rb": "ruby"}


def translate(program, target):
    key = ALIASES.get(target.lower(), target.lower())
    if key not in TARGETS:
        raise ValueError(f"linguagem desconhecida: {target!r} (use: {', '.join(TARGETS)})")
    return TARGETS[key]().generate(program)
