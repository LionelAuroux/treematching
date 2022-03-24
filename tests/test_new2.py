
import logging

log = logging.getLogger(__file__)

def simplifyNeg(node):
    log.info(f"simplifyNeg {node}")
    match node:
        case ("-", ("-", expr)):
            res = expr
            log.info(f"{'>' * 10} simplifyNeg -- = {res}")
            return res
        case ("-", int() as expr):
            res = -expr
            log.info(f"{'>' * 10} simplifyNeg - = {res}")
            return res
        case ("-", ("+", int() as expr)):
            res = -expr
            log.info(f"{'>' * 10} simplifyNeg -+ = {res}")
            return res
        case ("+", ("-", int() as expr)):
            res = -expr
            log.info(f"{'>' * 10} simplifyNeg +- = {res}")
            return res
        case _:
            return node

def castToInt(node):
    log.info(f"castToInt {repr(node)}")
    match node:
        case str() as expr:
            try:
                res = int(expr)
                log.info(f"{'>' * 10} castToInt = {res}")
                return res
            except ValueError:
                # unable to cast, so don't touch the variable
                return node
        case _:
            return node

def simplifyPlus(node):
    log.info(f"simplifyPlus {node}")
    match node:
        case ("+", int() as left, int() as right):
            res = left + right
            log.info(f"{'>' * 10} simplifyPlus = {res}")
            return res
        case _:
            return node

def calc(node):
    log.info(f"Node {node}")
    ctx = {'a': 2600, 'b': 42}
    match node:
        case ("+", left, right):
            res = calc(left) + calc(right)
        case ("-", left, right):
            res = calc(left) - calc(right)
        case ("*", left, right):
            res = calc(left) * calc(right)
        case ("/", left, right):
            res = calc(left) / calc(right)
        case ("%", left, right):
            res = calc(left) % calc(right)
        case ("-", expr):
            res = - calc(expr)
        case ("+", expr):
            res = calc(expr)
        case int() as expr:
            res = expr
        case str() as expr:
            res = ctx[expr]
        case _ as err:
            raise RuntimeError(f"Unknown {err}")
    log.info(f"partial {res}")
    return res

def apply(fn, node):
    from treematching.transform import fixpoint, cache_node
    log.info(f"Apply {node}")
    match node:
        case (str() as a, b, c):
            b = fixpoint(apply, fn, b)
            c = fixpoint(apply, fn, c)
            return cache_node(a, b, c)
        case (str() as a, b):
            b = fixpoint(apply, fn, b)
            return cache_node(a, b)
        case _ as expr:
            return node

def test_base():
    from treematching.transform import fixpoint, ListFun
    ast = ("*", ("+", ("-", 4), "6"), ("-", ("+", ("/", 'b', 2), ("-", ("-", ('-', 'a', ('+', '1000', 1032)))))))
    log.info("BAST: {ast}")
    ast = fixpoint(apply, ListFun(castToInt, simplifyPlus, simplifyNeg), ast)
    log.info(f"FINAL: {ast}")
    r = calc(ast)
    log.info(f"RES: {r}")
    assert type(r) == float
    assert r == -1178.0
