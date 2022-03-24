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


def compose(walk, fn, node):
    log.info(f"compose {node}")
    #return walk(fn, fn(node)) # top-down
    return fn(walk(fn, node)) # bottom-up


cache_compose = {}
def fixpoint(walk, fn, node):
    global cache_compose
    log.info(f"fixpoint {node}")
    n = node
    while True:
        iw = id(walk)
        ifn = id(fn)
        inode = id(n)
        log.info(f"(ifn, inode) == {(ifn, inode)}")
        if (iw, ifn, inode) in cache_compose:
            log.info(f"end fixpoint {n}")
            return n
        else:
            n = compose(walk, fn, n)
            cache_compose[(iw, ifn, inode)] = n

cache_nodes = {}
def cache_node(*n):
    global cache_nodes
    idls = []
    for it in n:
        idls.append(id(it))
    k = tuple(idls)
    if k not in cache_nodes:
        cache_nodes[k] = n
    return cache_nodes[k]
