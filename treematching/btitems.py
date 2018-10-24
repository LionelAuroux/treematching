"""
    Behavior Tree Items...

    All what you need to construct your patterns...
"""

from treematching.matchcontext import *
from treematching.conditions import Condition
from treematching.debug import *

class BTItem:
    """
    Base class for all items of a pattern
    """
    def do(self, data, ctx) -> State:
        raise RuntimeError("must be implemented")

class Expr(BTItem):
    """
    Pattern that took one argument
    """
    def __init__(self, expr=None):
        self.expr = expr

class Pair(BTItem):
    """
    Pattern that took two argument
    """
    def __init__(self, first, second=None):
        self.first = first
        self.second = second

class Component(BTItem):
    """
    Pattern that took many argument
    """
    def __init__(self, *subs):
        self.subs = subs

    def do_template(self, t, data, ctx):
        ctx.init_state(self)
        log("%s %s" % (t.upper(), ctx.state))
        if ctx.state == 'enter':
            if ('enter_%s' % t) != data[Pos.TYPE]:
                return ctx.set_res(State.FAILED)
            ctx.state = t
            ctx.init_subs(self.subs)
            ## TODO: must get a correct uid
            ctx.uid = data[Pos.UID]
            return ctx.set_res(State.RUNNING)
        if ctx.state == t:
            # return to the attrs branch
            # calcul if we do a complete match
            if data[Pos.UID] == ctx.uid:
                log("UID: %s" % ctx.uid)
                log("data[UID]: %s" % data[Pos.UID])
                nbsuccess = 0
                for sub_ctx in ctx.subs:
                    if sub_ctx.res == State.SUCCESS and sub_ctx.uid[:-1] == ctx.uid:
                        nbsuccess += 1
                if nbsuccess == len(self.subs):
                    # continue
                    if t == data[Pos.TYPE]:
                        # strict
                        if self.strict and len(self.subs) != len(data[Pos.ARG]):
                            return ctx.set_res(State.FAILED)
                        log("Match %s" % t.upper())
                        return ctx.set_res(State.SUCCESS)
                return ctx.set_res(State.FAILED)
            # here // match
            for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                if sub_ctx.res == State.RUNNING:
                    res = sub_bt.do(data, sub_ctx)
                if sub_ctx.res == State.FAILED:
                    sub_ctx.state = 'enter'
                    sub_ctx.res = State.RUNNING
            # I don't have finish
            return ctx.set_res(State.RUNNING)

##########

class Capture(Pair):
    def do(self, data, ctx) -> State:
        root = ctx.getroot()
        root.init_capture()
        ctx.init_second()
        res = self.second.do(data, ctx.second)
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("CAPTURE %s" % self.first)
        root.capture[self.first] = data[Pos.ARG]
        return ctx.set_res(State.SUCCESS)

class Hook(Pair):
    def do(self, data, ctx) -> State:
        root = ctx.getroot()
        root.init_capture()
        ctx.init_second()
        res = self.second.do(data, ctx.second)
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("HOOK %s" % self.first)
        ## hook must return if a modification was done in the hook -> fixpoint
        if self.first(root.capture):
            root.nb_modif += 1
        return ctx.set_res(State.SUCCESS)

class Event(Pair):
    def do(self, data, ctx) -> State:
        root = ctx.getroot()
        root.init_event()
        ctx.init_second()
        res = self.second.do(data, ctx.second)
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("EVENT %s" % self.first)
        root.event |= {self.first}
        return ctx.set_res(State.SUCCESS)

##########

class Any(Component):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        if ctx.state == 'enter':
            log("ANY BEGIN %s" % repr(data))
            ctx.state = 'any'
            ctx.init_subs(self.subs)
            return ctx.set_res(State.RUNNING)
        if data[Pos.TYPE].startswith('enter_') and ctx.state == 'any':
            log("ANY CONTINUE %s" % repr(data))
            ctx.state = 'final'
            ctx.uid = data[Pos.UID]
        if ctx.state == 'final':
            if hasattr(ctx, 'end') and data[Pos.UID] == ctx.uid:
                # todo: count subs
                log("ANY UID: %s" % ctx.uid)
                log("ANY data[UID]: %s" % data[Pos.UID])
                nbsuccess = 0
                for sub_ctx in ctx.subs:
                    if sub_ctx.res == State.SUCCESS and sub_ctx.uid[:-1] == ctx.uid:
                        nbsuccess += 1
                if nbsuccess >= 1:
                    return ctx.set_res(State.SUCCESS)
                return ctx.set_res(State.FAILED)
            # here // match
            ctx.end = 0
            log("LEN SUBS %d LEN CTX %d" % (len(self.subs), len(ctx.subs)))
            for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                log("SUB CTX: %s" % sub_ctx.res)
                if sub_ctx.res == State.RUNNING:
                    res = sub_bt.do(data, sub_ctx)
                # if it's failed, we reset it
                if sub_ctx.res == State.FAILED:
                    sub_ctx.state = 'enter'
                    sub_ctx.res = State.RUNNING
        return ctx.set_res(State.RUNNING)

class Dict(Component):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do(self, data, ctx) -> State:
        return self.do_template('dict', data, ctx)

class Key(Pair):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("KEY %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            ctx.init_second()
            res = self.second.do(data, ctx.second)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            ctx.state = 'key'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'key':
            if 'key' == data[Pos.TYPE] and data[Pos.ARG] == self.first:
                log("Match Key %r" % self.first)
                return ctx.set_res(State.SUCCESS)
            log("KEY FAILED")
            return ctx.set_res(State.FAILED)

class AnyKey(Expr):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("ANYKEY %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            if self.expr:
                ctx.init_second()
                res = self.expr.do(data, ctx.second)
                if res != State.SUCCESS:
                    return ctx.set_res(res)
            ctx.state = 'key'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'key':
            if 'key' == data[Pos.TYPE]:
                log("Match AnyKey")
                return ctx.set_res(State.SUCCESS)
            log("ANYKEY FAILED")
            return ctx.set_res(State.FAILED)

class List(Component):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do(self, data, ctx) -> State:
        return self.do_template('list', data, ctx)

class Idx(Pair):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("IDX %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            ctx.init_second()
            res = self.second.do(data, ctx.second)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            ctx.state = 'idx'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'idx':
            if 'idx' == data[Pos.TYPE] and data[Pos.ARG] == self.first:
                log("Match Idx %r" % self.first)
                return ctx.set_res(State.SUCCESS)
            log("IDX FAILED")
            return ctx.set_res(State.FAILED)

class AnyIdx(Expr):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("ANYIDX %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            if self.expr:
                ctx.init_second()
                res = self.expr.do(data, ctx.second)
                if res != State.SUCCESS:
                    return ctx.set_res(res)
            ctx.state = 'idx'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'idx':
            if 'idx' == data[Pos.TYPE]:
                log("Match AnyIdx")
                return ctx.set_res(State.SUCCESS)
            log("ANYIDX FAILED")
            return ctx.set_res(State.FAILED)

class Attrs(Component):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do(self, data, ctx) -> State:
        return self.do_template('attrs', data, ctx)

class Attr(Pair):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("ATTR %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            ctx.init_second()
            res = self.second.do(data, ctx.second)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            ctx.state = 'attr'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'attr':
            if 'attr' == data[Pos.TYPE] and data[Pos.ARG] == self.first:
                log("Match Attr %r" % self.first)
                ctx.matched = self.first
                return ctx.set_res(State.SUCCESS)
            log("ATTR FAILED")
            return ctx.set_res(State.FAILED)

class AnyAttr(Expr):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("ANYATTR %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            if self.expr:
                ctx.init_second()
                res = self.expr.do(data, ctx.second)
                if res != State.SUCCESS:
                    return ctx.set_res(res)
            ctx.state = 'attr'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'attr':
            if 'attr' == data[Pos.TYPE]:
                log("Match AnyAttr")
                return ctx.set_res(State.SUCCESS)
            log("ANYATTR FAILED")
            return ctx.set_res(State.FAILED)

#####

class Value(Expr):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("VALUE %s" % (ctx.state))
        if ctx.state == 'enter':
            if self.expr:
                if 'value' == data[Pos.TYPE] and data[Pos.ARG] == self.expr:
                    log("Match Value %r" % self.expr)
                    return ctx.set_res(State.SUCCESS)
            log("VALUE FAILED")
            return ctx.set_res(State.FAILED)

class AnyValue(BTItem):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("ANYVALUE %s" % (ctx.state))
        if ctx.state == 'enter':
            if 'value' == data[Pos.TYPE]:
                log("Match AnyValue")
                return ctx.set_res(State.SUCCESS)
            log("ANYVALUE FAILED")
            return ctx.set_res(State.FAILED)

#####

class Type(Pair):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("TYPE %s" % ctx.state)
        if ctx.state == 'enter':
            if 'enter' != data[Pos.TYPE]:
                return ctx.set_res(State.FAILED)
            ctx.uid = data[Pos.UID]
            if self.second:
                ctx.state = 'sub'
            else:
                ctx.state = 'final'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'sub':
            ctx.init_second()
            res = self.second.do(data, ctx.second)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            ctx.state = 'final'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'final':
            log("%s ?? %s" % (type(data[Pos.ARG]).__name__, type(self.first).__name__))
            if 'type' == data[0] and type(data[Pos.ARG]) is self.first:
                log("Match Type %r" % self.first)
                return ctx.set_res(State.SUCCESS)
            log("TYPE FAILED")
            return ctx.set_res(State.FAILED)

class AnyType(Expr):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("ANYTYPE %s" % ctx.state)
        if ctx.state == 'enter':
            if 'enter' != data[Pos.TYPE]:
                return ctx.set_res(State.FAILED)
            ctx.uid = data[Pos.UID]
            if self.expr:
                ctx.state = 'sub'
            else:
                ctx.state = 'final'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'sub':
            ctx.init_second()
            res = self.expr.do(data, ctx.second)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            ctx.state = 'final'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'final':
            log("anytype %s" % type(data[Pos.ARG]))
            if 'type' == data[0]:
                log("Match AnyType")
                return ctx.set_res(State.SUCCESS)
            log("ANYTYPE FAILED")
            return ctx.set_res(State.FAILED)

class KindOf(Pair):
    def do(self, data, ctx) -> State:
        ctx.init_state(self)
        log("KIND %s" % ctx.state)
        if ctx.state == 'enter':
            if 'enter' != data[Pos.TYPE]:
                return ctx.set_res(State.FAILED)
            ctx.uid = data[Pos.UID]
            if self.second:
                ctx.state = 'sub'
            else:
                ctx.state = 'final'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'sub':
            ctx.init_second()
            res = self.second.do(data, ctx.second)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            ctx.state = 'final'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'final':
            log("KINDOF %s ?? %s" % (type(data[Pos.ARG]), repr(self.first)))
            if 'type' == data[0] and isinstance(data[Pos.ARG], self.first):
                log("Match Type %r" % self.first)
                return ctx.set_res(State.SUCCESS)
            log("KIND FAILED")
            return ctx.set_res(State.FAILED)
####

class Ancestor(Pair):
    def __init__(self, first, second=None, depth=0, strict=True):
        Pair.__init__(self, first, second)
        self.depth = depth

class Sibling(Component):
    def __init__(self, *subs, strict=True):
        # strict means that all siblings are at the same level
        # non strict, siblings have just a common ancestor
        Component.__init__(self, *subs)
        self.strict = strict
############
