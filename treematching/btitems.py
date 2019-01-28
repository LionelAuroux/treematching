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
    def do(self, data, ctx, user_data) -> State:
        raise RuntimeError("must be implemented")

    def __repr__(self) -> str:
        txt = type(self).__name__
        attrs = []
        if hasattr(self, 'subs'):
            attrs.append(".subs = %s" % (repr(self.subs)))
        if hasattr(self, 'expr'):
            attrs.append(".expr = %s" % (repr(self.expr)))
        if hasattr(self, 'first'):
            attrs.append(".first = %s" % (repr(self.first)))
        if hasattr(self, 'second'):
            attrs.append(".second = %s" % (repr(self.second)))
        txt += '(\n' + ', '.join(attrs) + '\n)'
        return txt

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

    def do_template(self, t, data, ctx, user_data):
        ctx.init_state(self)
        # to be notifying by subs
        ctx.matching = False
        if not hasattr(ctx, 'nbsuccess'):
            ctx.nbsuccess = 0
        log("%s %s" % (t.upper(), ctx.state))
        if ctx.state == 'enter':
            ctx.state = t
            ctx.init_subs(self.subs)
        if ctx.state == t:
            log("COMPONENT %s: [%s]" % (t, data))
            # calcul if we have finish
            if t == data[Pos.TYPE] and (not hasattr(ctx, 'uid') or data[Pos.UID] == ctx.uid):
                log("data[UID]: %s" % data[Pos.UID])
                log("LEN: %d ?? %d ?? %d" % (ctx.nbsuccess, len(self.subs), len(data[Pos.ARG])))
                if ctx.nbsuccess == len(self.subs):
                    # strict
                    if self.strict and len(self.subs) != len(data[Pos.ARG]):
                        return ctx.set_res(State.FAILED)
                    log("Match %s" % t.upper())
                    return ctx.set_res(State.SUCCESS)
                return ctx.set_res(State.FAILED)
            log("check subs")
            # here // match
            ctx.nbsuccess = 0
            ctx.nbrunning = 0
            for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                # tick only running BT
                if sub_ctx.res == State.RUNNING:
                    # deeper function could modify the current ctx.matching
                    res = sub_bt.do(data, sub_ctx, user_data)
                # count after tick
                if sub_ctx.res == State.RUNNING:
                    ctx.nbrunning += 1
                if sub_ctx.res == State.SUCCESS:
                    log("SUBS OK")
                    # take the first uid as ref
                    if not hasattr(ctx, 'uid'):
                        ctx.uid = sub_ctx.uid[:-1]
                    #must be at the same level
                    if ctx.uid != sub_ctx.uid[:-1]:
                        log("NOT AT THE LEVEL %s ?? %s" % (ctx.uid, sub_ctx.uid[:-1]))
                        sub_ctx.reset_tree()
                    else:
                        ctx.nbsuccess += 1
            # I don't have finish
            log("CHECK MATCHING %d: %s & nbsuccess %d & nbrunning %d" % (id(ctx), ctx.matching, ctx.nbsuccess, ctx.nbrunning))
            # on a partial match, resync the failed
            if ctx.matching or ctx.nbrunning or ctx.nbsuccess:
                log("Need TO RESET")
                for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                    if sub_ctx.res == State.FAILED:
                        log("RESET %d" % id(sub_ctx))
                        # reset
                        sub_ctx.reset_tree()
                return ctx.set_res(State.RUNNING)
            return ctx.set_res(State.FAILED)

##########

class Capture(Pair):
    def do(self, data, ctx, user_data) -> State:
        root = ctx.getroot()
        root.init_capture()
        ctx.init_second()
        log("CAPTURE SECOND %d" % id(ctx.second))
        res = self.second.do(data, ctx.second, user_data)
        log("CAPTURE RES: %s ID %d" % (res, id(ctx.second)))
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("CAPTURE %s" % self.first)
        root.capture[self.first] = data[Pos.ARG]
        return ctx.set_res(State.SUCCESS)

class Hook(Pair):
    def do(self, data, ctx, user_data) -> State:
        root = ctx.getroot()
        root.init_capture()
        ctx.init_second()
        res = self.second.do(data, ctx.second, user_data)
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("HOOK %s" % self.first)
        ## hook must return if a modification was done in the hook -> fixpoint
        if self.first(root.capture, user_data):
            root.nb_modif += 1
        return ctx.set_res(State.SUCCESS)

class Event(Pair):
    def do(self, data, ctx, user_data) -> State:
        root = ctx.getroot()
        root.init_event()
        ctx.init_second()
        res = self.second.do(data, ctx.second, user_data)
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("EVENT %s" % self.first)
        root.event |= {self.first}
        return ctx.set_res(State.SUCCESS)

##########

class Any(Component): #!!!!!!!!!!!!!!!!!!!
    def do(self, data, ctx, user_data) -> State:
        #TODO: must be review and found how to don't use it
        ctx.init_state(self)
        if ctx.state == 'enter':
            log("ANY BEGIN %s" % repr(data))
            ctx.state = 'final'
            ctx.init_subs(self.subs)
        if ctx.state == 'final':
            if hasattr(ctx, 'end') and 'type' == data[Pos.TYPE]:
                # todo: count subs
                log("ANY data[UID]: %s" % data[Pos.UID])
                nbsuccess = 0
                for sub_ctx in ctx.subs:
                    if sub_ctx.res == State.SUCCESS:
                        nbsuccess += 1
                log("ANY NBSUCCESS %d" % nbsuccess)
                log("ANY ID %d" % id(ctx))
                if nbsuccess >= 1:
                    ctx.uid = data[Pos.UID]
                    return ctx.set_res(State.SUCCESS)
                log("ANY FAILED")
                return ctx.set_res(State.FAILED)
            # here // match
            ctx.nbsuccess = 0
            ctx.nbrunning = 0
            #ctx.end = 0
            log("LEN SUBS %d LEN CTX %d" % (len(self.subs), len(ctx.subs)))
            for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                log("SUB CTX: %s" % sub_ctx.res)
                if sub_ctx.res == State.RUNNING:
                    res = sub_bt.do(data, sub_ctx, user_data)
                # count after tick
                if sub_ctx.res == State.RUNNING:
                    ctx.nbrunning += 1
                if sub_ctx.res == State.SUCCESS:
                    ctx.nbsuccess += 1
                # if it's failed, we reset it
                if sub_ctx.res == State.FAILED:
                    sub_ctx.reset_tree()
        return ctx.set_res(State.RUNNING)

class Dict(Component):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do(self, data, ctx, user_data) -> State:
        return self.do_template('dict', data, ctx, user_data)

class AnyDict(BTItem):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYDCIT %s" % ctx.state)
        if ctx.state == 'enter':
            if 'dict' == data[Pos.TYPE]:
                log("ANYDICT SUCCESS ID %d" % (id(ctx)))
                ctx.uid = data[Pos.UID] #!!!!!
                return ctx.set_res(State.SUCCESS)
        return ctx.set_res(State.FAILED)

class Key(Pair):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("KEY %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do(data, ctx.second, user_data)
                if res != State.SUCCESS:
                    return ctx.set_res(res)
            ctx.state = 'key'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'key':
            if 'key' == data[Pos.TYPE] and data[Pos.ARG] == self.first:
                log("Match Key %r" % self.first)
                ctx.uid = data[Pos.UID] #!!!!
                return ctx.set_res(State.SUCCESS)
            log("KEY FAILED")
            return ctx.set_res(State.FAILED)

class AnyKey(Expr):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYKEY %s" % ctx.state)
        if ctx.state == 'enter':
            if self.expr:
                ctx.init_second()
                if ctx.second.res != State.SUCCESS:
                    res = self.expr.do(data, ctx.second, user_data)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
            ctx.state = 'key'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'key':
            if 'key' == data[Pos.TYPE]:
                log("Match AnyKey")
                ctx.uid = data[Pos.UID]
                return ctx.set_res(State.SUCCESS)
            log("ANYKEY FAILED")
            return ctx.set_res(State.FAILED)

class List(Component):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do(self, data, ctx, user_data) -> State:
        return self.do_template('list', data, ctx, user_data)

class AnyList(BTItem):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYLIST %s" % ctx.state)
        if ctx.state == 'enter':
            if 'list' == data[Pos.TYPE]:
                log("ANYLIST SUCCESS ID %d" % (id(ctx)))
                ctx.uid = data[Pos.UID]
                return ctx.set_res(State.SUCCESS)
        # I don't have finish
        return ctx.set_res(State.FAILED)

class Idx(Pair):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("IDX %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do(data, ctx.second, user_data)
                if res != State.SUCCESS:
                    return ctx.set_res(res)
            ctx.state = 'idx'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'idx':
            if 'idx' == data[Pos.TYPE] and data[Pos.ARG] == self.first:
                log("Match Idx %r" % self.first)
                ctx.uid = data[Pos.UID] #!!!!!!!
                return ctx.set_res(State.SUCCESS)
            log("IDX FAILED")
            return ctx.set_res(State.FAILED)

class AnyIdx(Expr):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYIDX %s" % ctx.state)
        if ctx.state == 'enter':
            if self.expr:
                ctx.init_second()
                if ctx.second.res != State.SUCCESS:
                    res = self.expr.do(data, ctx.second, user_data)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
            ctx.state = 'idx'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'idx':
            if 'idx' == data[Pos.TYPE]:
                log("Match AnyIdx")
                ctx.uid = data[Pos.UID] #!!!!!
                return ctx.set_res(State.SUCCESS)
            log("ANYIDX FAILED")
            return ctx.set_res(State.FAILED)

class Attrs(Component):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do(self, data, ctx, user_data) -> State:
        return self.do_template('attrs', data, ctx, user_data)

# TODO: AnyAttrs

class Attr(Pair):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ATTR %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do(data, ctx.second, user_data)
                if res != State.SUCCESS:
                    return ctx.set_res(res)
            ctx.state = 'attr'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'attr':
            if 'attr' == data[Pos.TYPE] and data[Pos.ARG] == self.first:
                log("Match Attr %r" % self.first)
                ctx.matched = self.first
                ctx.uid = data[Pos.UID] #!!!!
                ctx.when = data[Pos.ARG]
                return ctx.set_res(State.SUCCESS)
            log("ATTR FAILED")
            return ctx.set_res(State.FAILED)

class AnyAttr(Expr):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYATTR %s" % ctx.state)
        if ctx.state == 'enter':
            if self.expr:
                ctx.init_second()
                if ctx.second.res != State.SUCCESS:
                    res = self.expr.do(data, ctx.second, user_data)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
            ctx.state = 'attr'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'attr':
            if 'attr' == data[Pos.TYPE]:
                log("Match AnyAttr")
                ctx.uid = data[Pos.UID] #!!!
                return ctx.set_res(State.SUCCESS)
            log("ANYATTR FAILED")
            return ctx.set_res(State.FAILED)

#####

class Value(Expr):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("VALUE %s" % (ctx.state))
        if ctx.state == 'enter':
            if self.expr:
                if 'value' == data[Pos.TYPE] and data[Pos.ARG] == self.expr:
                    log("Match Value %r" % self.expr)
                    ctx.uid = data[Pos.UID]
                    return ctx.set_res(State.SUCCESS)
            log("VALUE FAILED")
            return ctx.set_res(State.FAILED)

class AnyValue(BTItem):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYVALUE %s" % (ctx.state))
        if ctx.state == 'enter':
            if 'value' == data[Pos.TYPE]:
                log("Match AnyValue")
                ctx.uid = data[Pos.UID]
                ctx.when = data[Pos.ARG]
                return ctx.set_res(State.SUCCESS)
            log("ANYVALUE FAILED")
            return ctx.set_res(State.FAILED)

#####

class Type(Pair):
    def __init__(self, *subs, kindof=False):
        if len(subs) not in [1, 2, 3, 4]:
            raise TypeError("Type take at least one argument at most four argument")
        self.first = subs[0]
        self.second = None
        self.third = None
        self.four = None
        self.kindof = kindof
        if len(subs) > 1:
            self.second = subs[1]
        if len(subs) > 2:
            # second must be List or Dict
            self.third = subs[2]
        if len(subs) > 3:
            # second and thirs must be List or Dict
            self.four = subs[3]

    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("TYPE %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            if self.second:
                ctx.state = 'sub'
            else:
                ctx.state = 'final'
            log("TYPE CHANGE TYPE %s" % ctx.state)
        if ctx.state == 'sub':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do(data, ctx.second, user_data)
                if res != State.SUCCESS:
                    return ctx.set_res(res)
            ctx.state = 'final'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'final':
            log("%s ?? %s" % (type(data[Pos.ARG]).__name__, type(self.first).__name__))
            cmp_type = type(data[Pos.ARG]) is self.first
            if self.kindof:
                cmp_type = issubclass(type(data[Pos.ARG]), self.first)
            if 'type' == data[0] and cmp_type:
                log("Match Type %r" % self.first)
                ctx.uid = data[Pos.UID]
                ctx.when = type(data[Pos.ARG]).__name__
                return ctx.set_res(State.SUCCESS)
            log("TYPE FAILED")
            return ctx.set_res(State.FAILED)

class AnyType(Expr):
    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYTYPE %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            if self.expr:
                ctx.state = 'sub'
            else:
                ctx.state = 'final'
            log("ANYTYPE CHANGE TYPE %s" % ctx.state)
        if ctx.state == 'sub':
            ctx.init_second()
            res = self.expr.do(data, ctx.second, user_data)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            ctx.state = 'final'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'final':
            log("anytype %s" % type(data[Pos.ARG]))
            if 'type' == data[0]:
                log("Match AnyType")
                ctx.uid = data[Pos.UID]
                ctx.when = type(data[Pos.ARG])
                return ctx.set_res(State.SUCCESS)
            log("ANYTYPE FAILED")
            return ctx.set_res(State.FAILED)

def KindOf(*subs):
    res = Type(*subs, kindof=True)
    return res

"""
class KindOf(Pair):
    def __init__(self, *subs):
        if len(subs) == 0:
            raise TypeError("Type take at least 1 argument, and max 3")
        self.first = subs[0]
        self.subs = None
        if len(subs) > 1:
            self.subs = subs[1:]
        # TODO: len(subs) > 3 ERROR
        # TODO: len(subs) == 3 first -> (Any)?(List|Dict), second -> Attrs

    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        # to be notifying by subs
        ctx.matching = False
        if ctx.state == 'enter':
            # only test?
            ctx.uid = None
            if self.subs:
                ctx.init_subs(self.subs)
                ctx.state = 'sub'
                ctx.current = 0
            else:
                ctx.state = 'final'

        log("KIND %s" % ctx.state)
        log("KIND %d CTXUID %s CTXCURRENT %d/%d" % (id(ctx), repr(ctx.uid), ctx.current, len(self.subs)))
        log("KIND CTXUID2 %s" % repr(data[Pos.UID]))
        if (ctx.uid is not None and ctx.uid == data[Pos.UID]) or ctx.current == len(self.subs):
            ctx.state = 'final'
        if ctx.state == 'sub':
            # here // match
            ctx.nbsuccess = 0
            ctx.nbrunning = 0
            log("LEN SUBS %d LEN CTX %d" % (len(self.subs), len(ctx.subs)))
            sub_bt, sub_ctx = (self.subs[ctx.current], ctx.subs[ctx.current])
            log("SUB CTX: %s" % sub_ctx.res)
            if sub_ctx.res == State.RUNNING:
                res = sub_bt.do(data, sub_ctx, user_data)
            log("RES SUB CTX: %s" % sub_ctx.res)
            # count after tick
            if sub_ctx.res == State.RUNNING:
                ctx.nbrunning += 1
            if sub_ctx.res == State.SUCCESS:
                log("SUCCESS OF %d SO %d" % (id(sub_ctx), id(ctx)))
                ctx.current += 1
                ctx.nbsuccess += 1
                if ctx.uid is None:
                    ctx.uid = sub_ctx.uid
                    log("SUCCESS %d: %s" % (id(ctx), repr(ctx.uid)))
                elif ctx.uid != data[Pos.UID]:
                    ctx.nbsuccess -= 1
                    sub_ctx.res = State.FAILED
            if ctx.matching:
                ctx.matching = False
                return ctx.set_res(State.RUNNING)
            return ctx.set_res(sub_ctx.res)
        if ctx.state == 'final':
            log("KINDOF %s ?? %s" % (type(data[Pos.ARG]), repr(self.first)))
            if 'type' == data[0] and isinstance(data[Pos.ARG], self.first):
                if self.subs and ctx.nbsuccess == 0:
                    return ctx.set_res(State.FAILED)
                log("Match Type %r" % self.first)
                return ctx.set_res(State.SUCCESS)
            log("KIND FAILED")
            return ctx.set_res(State.FAILED)
####
"""

class Ancestor(Pair):
    def __init__(self, first, second, depth=1, strict=True):
        """
            strict means that the depth between the ancestor and the child is exactly at depth
            otherwise it's greater than or equal
        """
        Pair.__init__(self, first, second)
        self.depth = depth
        self.strict = strict

    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        ctx.init_first()
        ctx.init_second()
        log("Ancestor %s" % ctx.state)
        if ctx.state == 'enter':
            res = self.second.do(data, ctx.second, user_data)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            log("Ancestor Found Child")
            ctx.state = 'final'
            ctx.uid = data[Pos.UID]
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'final':
            log("Ancestor begin search")
            res = self.first.do(data, ctx.first, user_data)
            log("Ancestor search %s" % res)
            if res != State.SUCCESS:
                return ctx.set_res(State.RUNNING)
            # check depth
            new_end = len(data[Pos.UID])
            log("Ancestor check %s : %s" % (ctx.uid[:new_end], data[Pos.UID]))
            if ctx.uid[:new_end] == data[Pos.UID]:
                if len(ctx.uid) == new_end + self.depth or (not self.strict and len(ctx.uid) >= new_end + self.depth):
                    return ctx.set_res(State.SUCCESS)
                # too near reset first part
                elif len(ctx.uid) < new_end + self.depth:
                    ctx.first.reset_tree()
                    return ctx.set_res(State.RUNNING)
            return ctx.set_res(State.FAILED)
        return ctx.set_res(State.RUNNING)

class Sibling(BTItem):
    def __init__(self, *subs, strict=True):
        """
            strict means that all siblings are at the same level
            non strict, siblings have just a common ancestor
        """
        self.subs = subs
        self.strict = strict

    def do(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        # to be notifying by subs
        ctx.matching = False
        if not hasattr(ctx, 'nbsuccess'):
            ctx.nbsuccess = 0
        log("Sibling %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.state = 'subs'
            ctx.init_subs(self.subs)
        if ctx.state == 'subs':
            log("COMPONENT [%s]" % repr(data))
            # here // match
            ctx.nbsuccess = 0
            ctx.nbrunning = 0
            for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                # tick only running BT
                if sub_ctx.res == State.RUNNING:
                    # deeper function could modify the current ctx.matching
                    res = sub_bt.do(data, sub_ctx, user_data)
                # count after tick
                if sub_ctx.res == State.RUNNING:
                    ctx.nbrunning += 1
                if sub_ctx.res == State.SUCCESS:
                    log("SUBS OK")
                    ctx.nbsuccess += 1
            # I have finish
            if ctx.nbsuccess == len(self.subs):
                # TODO: need to check uid
                return ctx.set_res(State.SUCCESS)
            # I don't have finish
            log("CHECK SIBLING %d: %s & nbsuccess %d & nbrunning %d" % (id(ctx), ctx.matching, ctx.nbsuccess, ctx.nbrunning))
            # on a partial match, resync the failed
            if ctx.matching or ctx.nbrunning or ctx.nbsuccess:
                log("Need TO RESET")
                for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                    if sub_ctx.res == State.FAILED:
                        log("RESET %d" % id(sub_ctx))
                        # reset
                        sub_ctx.reset_tree()
                return ctx.set_res(State.RUNNING)
            return ctx.set_res(State.FAILED)

############
