"""Interpretador (tree-walking) da linguagem CACHOEIRA."""
from . import ast_nodes as ast
from .errors import CachoeiraRuntimeError


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def declare(self, name, value):
        self.vars[name] = value

    def get(self, name, line):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise CachoeiraRuntimeError(f"Linha {line}: variável '{name}' não existe — memo aí não foi declarado")

    def assign(self, name, value, line):
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        raise CachoeiraRuntimeError(f"Linha {line}: variável '{name}' não existe — memo aí não foi declarado")


class Function:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure


class Interpreter:
    def __init__(self, out=print):
        self.globals = Environment()
        self.out = out

    def run(self, program: ast.Program):
        self.exec_block(program.statements, self.globals)

    # ---------- execução de statements ----------
    def exec_block(self, statements, env):
        for stmt in statements:
            self.exec_stmt(stmt, env)

    def exec_stmt(self, stmt, env):
        method = getattr(self, f"exec_{type(stmt).__name__}")
        method(stmt, env)

    def exec_VarDecl(self, stmt, env):
        value = self.eval(stmt.expr, env)
        env.declare(stmt.name, value)

    def exec_Assign(self, stmt, env):
        value = self.eval(stmt.expr, env)
        env.assign(stmt.name, value, stmt.line)

    def exec_Print(self, stmt, env):
        value = self.eval(stmt.expr, env)
        self.out(to_display(value))

    def exec_If(self, stmt, env):
        if is_truthy(self.eval(stmt.cond, env)):
            self.exec_block(stmt.then_body, Environment(env))
        else:
            self.exec_block(stmt.else_body, Environment(env))

    def exec_While(self, stmt, env):
        while is_truthy(self.eval(stmt.cond, env)):
            self.exec_block(stmt.body, Environment(env))

    def exec_Try(self, stmt, env):
        try:
            self.exec_block(stmt.try_body, Environment(env))
        except CachoeiraRuntimeError:
            self.exec_block(stmt.catch_body, Environment(env))

    def exec_FuncDef(self, stmt, env):
        env.declare(stmt.name, Function(stmt.name, stmt.params, stmt.body, env))

    def exec_Return(self, stmt, env):
        value = self.eval(stmt.expr, env) if stmt.expr is not None else None
        raise ReturnSignal(value)

    def exec_ExprStmt(self, stmt, env):
        self.eval(stmt.expr, env)

    # ---------- avaliação de expressões ----------
    def eval(self, node, env):
        method = getattr(self, f"eval_{type(node).__name__}")
        return method(node, env)

    def eval_Literal(self, node, env):
        return node.value

    def eval_Var(self, node, env):
        return env.get(node.name, node.line)

    def eval_UnaryOp(self, node, env):
        value = self.eval(node.expr, env)
        if node.op == "-":
            return -value
        if node.op == "!":
            return not is_truthy(value)
        raise CachoeiraRuntimeError(f"Linha {node.line}: operador unário desconhecido '{node.op}'")

    def eval_BinOp(self, node, env):
        if node.op == "&&":
            left = self.eval(node.left, env)
            if not is_truthy(left):
                return False
            return is_truthy(self.eval(node.right, env))
        if node.op == "||":
            left = self.eval(node.left, env)
            if is_truthy(left):
                return True
            return is_truthy(self.eval(node.right, env))

        left = self.eval(node.left, env)
        right = self.eval(node.right, env)
        op = node.op
        try:
            if op == "+":
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise CachoeiraRuntimeError(
                        f"Linha {node.line}: divisão por zero — nem por deus irmão isso vai colar"
                    )
                return left / right
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
        except TypeError as exc:
            raise CachoeiraRuntimeError(f"Linha {node.line}: operação inválida ({exc})")
        raise CachoeiraRuntimeError(f"Linha {node.line}: operador desconhecido '{op}'")

    def eval_Call(self, node, env):
        args = [self.eval(a, env) for a in node.args]

        if node.name in BUILTINS:
            return BUILTINS[node.name](args, node.line)

        func = env.get(node.name, node.line)
        if not isinstance(func, Function):
            raise CachoeiraRuntimeError(f"Linha {node.line}: '{node.name}' não é uma função")
        if len(args) != len(func.params):
            raise CachoeiraRuntimeError(
                f"Linha {node.line}: '{node.name}' espera {len(func.params)} argumento(s), recebeu {len(args)}"
            )

        call_env = Environment(func.closure)
        for name, value in zip(func.params, args):
            call_env.declare(name, value)

        try:
            self.exec_block(func.body, call_env)
        except ReturnSignal as ret:
            return ret.value
        return None


def is_truthy(value):
    if value is None:
        return False
    return bool(value)


def to_display(value):
    if value is True:
        return "FI"
    if value is False:
        return "NUNCA NA VIDA"
    if value is None:
        return "NUNCA NA VIDA"
    return str(value)


def _builtin_tamanho(args, line):
    if len(args) != 1:
        raise CachoeiraRuntimeError(f"Linha {line}: TAMANHO espera 1 argumento")
    return len(args[0])


BUILTINS = {
    "TAMANHO": _builtin_tamanho,
}
