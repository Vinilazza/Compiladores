"""Parser recursivo-descendente da linguagem CACHOEIRA."""
from . import ast_nodes as ast
from .errors import CachoeiraSyntaxError

BLOCK_ENDERS = {"END", "ELSE", "CATCH", "EOF"}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- utilidades ----------
    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def check(self, ttype):
        return self.peek().type == ttype

    def match(self, *ttypes):
        if self.peek().type in ttypes:
            return self.advance()
        return None

    def expect(self, ttype, msg=None):
        if self.check(ttype):
            return self.advance()
        tok = self.peek()
        raise CachoeiraSyntaxError(
            msg or f"Linha {tok.line}: esperava {ttype}, achei {tok.type} ({tok.value!r}) — só por deus irmão"
        )

    # ---------- programa ----------
    def parse_program(self):
        statements = []
        while not self.check("EOF"):
            statements.append(self.parse_statement())
        return ast.Program(statements)

    def parse_block(self):
        statements = []
        while self.peek().type not in BLOCK_ENDERS:
            statements.append(self.parse_statement())
        return statements

    # ---------- statements ----------
    def parse_statement(self):
        tok = self.peek()

        if tok.type == "VAR":
            return self.parse_var_decl()
        if tok.type == "PRINT":
            return self.parse_print()
        if tok.type == "IF":
            return self.parse_if()
        if tok.type == "WHILE_OR_TRY":
            return self.parse_while_or_try()
        if tok.type == "FUNC":
            return self.parse_func_def()
        if tok.type == "RETURN":
            return self.parse_return()
        return self.parse_expr_stmt()

    def parse_var_decl(self):
        line = self.expect("VAR").line
        name = self.expect("IDENT").value
        self.expect("EQ")
        expr = self.parse_expr()
        return ast.VarDecl(name, expr, line)

    def parse_print(self):
        line = self.expect("PRINT").line
        expr = self.parse_expr()
        return ast.Print(expr, line)

    def parse_if(self):
        line = self.expect("IF").line
        self.expect("LPAREN")
        cond = self.parse_expr()
        self.expect("RPAREN")
        then_body = self.parse_block()
        else_body = []
        if self.match("ELSE"):
            else_body = self.parse_block()
        self.expect("END")
        return ast.If(cond, then_body, else_body, line)

    def parse_while_or_try(self):
        line = self.expect("WHILE_OR_TRY").line
        if self.match("TENTANDO"):
            try_body = self.parse_block()
            self.expect("CATCH")
            catch_body = self.parse_block()
            self.expect("END")
            return ast.Try(try_body, catch_body, line)

        self.expect("LPAREN")
        cond = self.parse_expr()
        self.expect("RPAREN")
        body = self.parse_block()
        self.expect("END")
        return ast.While(cond, body, line)

    def parse_func_def(self):
        line = self.expect("FUNC").line
        name = self.expect("IDENT").value
        self.expect("LPAREN")
        params = []
        if not self.check("RPAREN"):
            params.append(self.expect("IDENT").value)
            while self.match("COMMA"):
                params.append(self.expect("IDENT").value)
        self.expect("RPAREN")
        body = self.parse_block()
        self.expect("END")
        return ast.FuncDef(name, params, body, line)

    def parse_return(self):
        line = self.expect("RETURN").line
        expr = None
        if self.peek().type not in BLOCK_ENDERS and self.peek().type not in (
            "VAR", "PRINT", "IF", "WHILE_OR_TRY", "FUNC", "RETURN",
        ):
            expr = self.parse_expr()
        return ast.Return(expr, line)

    def parse_expr_stmt(self):
        line = self.peek().line
        if self.check("IDENT") and self.tokens[self.pos + 1].type == "EQ":
            name = self.advance().value
            self.expect("EQ")
            expr = self.parse_expr()
            return ast.Assign(name, expr, line)
        expr = self.parse_expr()
        return ast.ExprStmt(expr, line)

    # ---------- expressões (precedência) ----------
    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.check("OR"):
            line = self.advance().line
            right = self.parse_and()
            left = ast.BinOp("||", left, right, line)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.check("AND"):
            line = self.advance().line
            right = self.parse_equality()
            left = ast.BinOp("&&", left, right, line)
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while self.peek().type in ("EQEQ", "NEQ"):
            op_tok = self.advance()
            right = self.parse_comparison()
            left = ast.BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_comparison(self):
        left = self.parse_additive()
        while self.peek().type in ("LT", "GT", "LE", "GE"):
            op_tok = self.advance()
            right = self.parse_additive()
            left = ast.BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek().type in ("PLUS", "MINUS"):
            op_tok = self.advance()
            right = self.parse_multiplicative()
            left = ast.BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.peek().type in ("STAR", "SLASH"):
            op_tok = self.advance()
            right = self.parse_unary()
            left = ast.BinOp(op_tok.value, left, right, op_tok.line)
        return left

    def parse_unary(self):
        if self.peek().type in ("MINUS", "BANG"):
            op_tok = self.advance()
            expr = self.parse_unary()
            return ast.UnaryOp(op_tok.value, expr, op_tok.line)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()

        if tok.type == "NUMBER":
            self.advance()
            return ast.Literal(tok.value)
        if tok.type == "STRING":
            self.advance()
            return ast.Literal(tok.value)
        if tok.type == "TRUE":
            self.advance()
            return ast.Literal(True)
        if tok.type == "FALSE":
            self.advance()
            return ast.Literal(False)
        if tok.type == "LPAREN":
            self.advance()
            expr = self.parse_expr()
            self.expect("RPAREN")
            return expr
        if tok.type == "IDENT":
            name = self.advance().value
            if self.match("LPAREN"):
                args = []
                if not self.check("RPAREN"):
                    args.append(self.parse_expr())
                    while self.match("COMMA"):
                        args.append(self.parse_expr())
                self.expect("RPAREN")
                return ast.Call(name, args, tok.line)
            return ast.Var(name, tok.line)

        raise CachoeiraSyntaxError(
            f"Linha {tok.line}: token inesperado {tok.type} ({tok.value!r}) — sou de são paulo fi, isso não bate"
        )


def parse(tokens):
    return Parser(tokens).parse_program()
