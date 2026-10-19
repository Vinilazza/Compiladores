"""Nós da AST da linguagem CACHOEIRA."""


class Node:
    pass


class Program(Node):
    def __init__(self, statements):
        self.statements = statements


class VarDecl(Node):
    def __init__(self, name, expr, line):
        self.name = name
        self.expr = expr
        self.line = line


class Assign(Node):
    def __init__(self, name, expr, line):
        self.name = name
        self.expr = expr
        self.line = line


class Print(Node):
    def __init__(self, expr, line):
        self.expr = expr
        self.line = line


class If(Node):
    def __init__(self, cond, then_body, else_body, line):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body
        self.line = line


class While(Node):
    def __init__(self, cond, body, line):
        self.cond = cond
        self.body = body
        self.line = line


class Try(Node):
    def __init__(self, try_body, catch_body, line):
        self.try_body = try_body
        self.catch_body = catch_body
        self.line = line


class FuncDef(Node):
    def __init__(self, name, params, body, line):
        self.name = name
        self.params = params
        self.body = body
        self.line = line


class Return(Node):
    def __init__(self, expr, line):
        self.expr = expr
        self.line = line


class ExprStmt(Node):
    def __init__(self, expr, line):
        self.expr = expr
        self.line = line


class BinOp(Node):
    def __init__(self, op, left, right, line):
        self.op = op
        self.left = left
        self.right = right
        self.line = line


class UnaryOp(Node):
    def __init__(self, op, expr, line):
        self.op = op
        self.expr = expr
        self.line = line


class Literal(Node):
    def __init__(self, value):
        self.value = value


class Var(Node):
    def __init__(self, name, line):
        self.name = name
        self.line = line


class Call(Node):
    def __init__(self, name, args, line):
        self.name = name
        self.args = args
        self.line = line
