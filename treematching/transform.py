import logging

log = logging.getLogger(__file__)

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
