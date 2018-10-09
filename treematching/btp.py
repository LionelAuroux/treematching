from treematching.matchcontext import *
from treematching.debug import *

class BTItem:
    def do(self, data, ctx) -> State:
        raise RuntimeError("must be implemented")

class Expr(BTItem):
    def __init__(self, expr=None):
        self.expr = expr

class Pair(BTItem):
    def __init__(self, first, second=None):
        self.first = first
        self.second = second

class Component(BTItem):
    def __init__(self, *subs):
        self.subs = subs

##########

class Capture(Pair):
    def do(self, data, ctx):
        root = ctx.getroot()
        root.init_capture()
        ctx.init_second()
        res = self.second.do(data, ctx.second)
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("CAPTURE %s" % data[Pos.ARG])
        root.capture[self.first] = data[Pos.ARG]
        return ctx.set_res(State.SUCCESS)

class Dict(Component):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do(self, data, ctx):
        ctx.init_state(self)
        log("DICT %s" % ctx.state)
        if ctx.state == 'enter':
            if 'enter_dict' != data[Pos.TYPE]:
                return ctx.set_res(State.FAILED)
            ctx.state = 'dict'
            ctx.init_subs(self.subs)
            ## TODO: must get a correct uid
            ctx.uid = data[Pos.UID]
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'dict':
            # return to the attrs branch
            # calcul if we do a complete match
            if data[Pos.UID] == ctx.uid:
                log("UID: %s" % ctx.uid)
                log("data[3]: %s" % data[Pos.UID])
                nbsuccess = 0
                for sub_ctx in ctx.subs:
                    if sub_ctx.res == State.SUCCESS and sub_ctx.uid[:-1] == ctx.uid:
                        nbsuccess += 1
                if nbsuccess == len(self.subs):
                    # continue
                    if 'dict' == data[Pos.TYPE]:
                        # strict
                        if self.strict and len(self.subs) != len(data[Pos.ARG]):
                            return ctx.set_res(State.FAILED)
                        log("Match DICT")
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

class Key(Pair):
    def do(self, data, ctx):
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
    def do(self, data, ctx):
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

    def do(self, data, ctx):
        ctx.init_state(self)
        log("LIST %s %s" % (ctx.state, data[Pos.TYPE]))
        if ctx.state == 'enter':
            if 'enter_list' != data[Pos.TYPE]:
                return ctx.set_res(State.FAILED)
            ctx.state = 'list'
            ctx.init_subs(self.subs)
            ## TODO: must get a correct uid
            ctx.uid = data[Pos.UID]
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'list':
            # return to the attrs branch
            # calcul if we do a complete match
            if data[Pos.UID] == ctx.uid:
                log("UID: %s" % ctx.uid)
                log("data[3]: %s" % data[Pos.UID])
                nbsuccess = 0
                for sub_ctx in ctx.subs:
                    if sub_ctx.res == State.SUCCESS and sub_ctx.uid[:-1] == ctx.uid:
                        nbsuccess += 1
                if nbsuccess == len(self.subs):
                    # continue
                    if 'list' == data[Pos.TYPE]:
                        log("strict %s len %d" % (self.strict, len(data[Pos.ARG])))
                        # strict
                        if self.strict and len(self.subs) != len(data[Pos.ARG]):
                            return ctx.set_res(State.FAILED)
                        log("Match LIST")
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

class Idx(Pair):
    def do(self, data, ctx):
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
    def do(self, data, ctx):
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

    def do(self, data, ctx):
        ctx.init_state(self)
        log("ATTRSUN %s" % ctx.state)
        if ctx.state == 'enter':
            if 'enter_attrs' != data[Pos.TYPE]:
                return ctx.set_res(State.FAILED)
            ctx.state = 'attrs'
            ctx.init_subs(self.subs)
            ## TODO: must get a correct uid
            ctx.uid = data[Pos.UID]
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'attrs':
            # return to the attrs branch
            # calcul if we do a complete match
            if data[Pos.UID] == ctx.uid:
                log("UID: %s" % ctx.uid)
                log("data[3]: %s" % data[Pos.UID])
                nbsuccess = 0
                for sub_ctx in ctx.subs:
                    if sub_ctx.res == State.SUCCESS and sub_ctx.uid[:-1] == ctx.uid:
                        nbsuccess += 1
                if nbsuccess == len(self.subs):
                    # continue
                    if 'attrs' == data[Pos.TYPE]:
                        # strict
                        if self.strict and len(self.subs) != len(data[Pos.ARG]):
                            return ctx.set_res(State.FAILED)
                        log("Match Attrs")
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

class Attr(Pair):
    def do(self, data, ctx):
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
    def do(self, data, ctx):
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
            log("%s ?? %s" % (type(data[Pos.ARG]).__name__, self.first))
            if 'type' == data[0] and type(data[Pos.ARG]).__name__ == self.first:
                log("Match Type %r" % self.first)
                return ctx.set_res(State.SUCCESS)
            log("TYPE FAILED")
            return ctx.set_res(State.FAILED)

############
