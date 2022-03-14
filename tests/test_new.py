import logging
import weakref as wr

log = logging.getLogger(__file__)

def simplifyNeg(node):
    log.info(f"simplifyNeg {node}")
    match node:
        case ["-", ["-", expr]]:
            return expr
        case ["-", int() as expr]:
            res = -expr
            log.info(f"{'>' * 10} simplifyNeg = {res}")
            return res
        case ["-", ["+", int() as expr]]:
            res = -expr
            log.info(f"{'>' * 10} simplifyNeg = {res}")
            return res
        case ["+", ["-", int() as expr]]:
            res = -expr
            log.info(f"{'>' * 10} simplifyNeg = {res}")
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

class ListFun:
    def __init__(self, *funcs):
        self.funcs = funcs

    def __call__(self, node):
        n = node
        for f in self.funcs:
            n = f(n)
            log.info(f"out {id(n)}")
        return n

def apply(fn, node):
    log.info(f"Apply {node}")
    match node:
        case [str() as a, b]:
            bid = id(b)
            b = fixpoint(fn, b)
            if bid == id(b):
                return node
            return [a, b]
        case [str() as a, b, c]:
            bid = id(b)
            cid = id(c)
            b = fixpoint(fn, b)
            c = fixpoint(fn, c)
            if bid == id(b) and cid == id(c):
                return node
            return [a, b, c]
        case _ as expr:
            return node

def compose(fn, node):
    log.info(f"compose {node}")
    #return apply(fn, fn(node)) # top-down
    return fn(apply(fn, node)) # bottom-up


cache_fixpoint = {}
def fixpoint(fn, node):
    global cache_fixpoint
    log.info(f"fixpoint {node}")
    n = node
    while True:
        ifn = id(fn)
        inode = id(n)
        log.info(f"(ifn, inode) == {(ifn, inode)}")
        if (ifn, inode) in cache_fixpoint:
            log.info(f"end fixpoint {n}")
            return n
        else:
            n = compose(fn, n)
            cache_fixpoint[(ifn, inode)] = n

def test_base():
    ast = ["*", ["+", ["-", 4], "6"], ["-", ["+", ["/", 'b', 2], ["-", ["-", ['-', 'a', ['+', '1000', 1032]]]]]]]
    log.info("BING: {ast}")
    ast = fixpoint(ListFun(castToInt, simplifyPlus, simplifyNeg), ast)
    log.info(f"CASTED: {ast}")
    r = calc(ast)
    log.info(f"RES: {r}")
    assert True
