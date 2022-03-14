import logging

log = logging.getLogger(__file__)

def simplifyNeg(node):
    log.info(f"simplifyNeg {node}")
    match node:
        case ["-", ["-", expr]]:
            res = expr
            log.info(f"{'>' * 10} simplifyNeg -- = {res}")
            return res
        case ["-", int() as expr]:
            res = -expr
            log.info(f"{'>' * 10} simplifyNeg - = {res}")
            return res
        case ["-", ["+", int() as expr]]:
            res = -expr
            log.info(f"{'>' * 10} simplifyNeg -+ = {res}")
            return res
        case ["+", ["-", int() as expr]]:
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
        case ["+", int() as left, int() as right]:
            res = left + right
            log.info(f"{'>' * 10} simplifyPlus = {res}")
            return res
        case _:
            return node

def calc(node):
    log.info(f"Node {node}")
    ctx = {'a': 2600, 'b': 42}
    match node:
        case [expr]:
            res = calc(expr)
        case ["+", left, right]:
            res = calc(left) + calc(right)
        case ["-", left, right]:
            res = calc(left) - calc(right)
        case ["*", left, right]:
            res = calc(left) * calc(right)
        case ["/", left, right]:
            res = calc(left) / calc(right)
        case ["%", left, right]:
            res = calc(left) % calc(right)
        case ["-", expr]:
            res = - calc(expr)
        case ["+", expr]:
            res = calc(expr)
        case int() as expr:
            res = expr
        case str() as expr:
            res = ctx[expr]
        case _ as err:
            raise RuntimeError(f"Unknown {err}")
    log.info(f"partial {res}")
    return res

def test_base():
    from treematching.transform import fixpoint, ListFun
    ast = ["*", ["+", ["-", 4], "6"], ["-", ["+", ["/", 'b', 2], ["-", ["-", ['-', 'a', ['+', '1000', 1032]]]]]]]
    log.info("BING: {ast}")
    ast = fixpoint(ListFun(castToInt, simplifyPlus, simplifyNeg), ast)
    log.info(f"CASTED: {ast}")
    r = calc(ast)
    log.info(f"RES: {r}")
    assert type(r) == float
    assert r == -1178.0
