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
    def do_up(self, data, ctx, user_data) -> State:
        raise RuntimeError("must be implemented")

    def do_down(self, data, ctx, user_data) -> State:
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

    def do_up_template_old(self, t, data, ctx, user_data):
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
                    res = sub_bt.do_up(data, sub_ctx, user_data)
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
            log("FAILED TO RESET")
            return ctx.set_res(State.FAILED)

    def do_up_template(self, t, data, ctx, user_data):
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
                    res = sub_bt.do_up(data, sub_ctx, user_data)
                # count after tick
                if sub_ctx.res == State.RUNNING:
                    ctx.nbrunning += 1
                # partial match
                if sub_ctx.res == State.SUCCESS:
                    log("SUBS OK")
                    # take the first uid as ref
                    if not hasattr(ctx, 'uid'):
                        ctx.uid = sub_ctx.uid[:-1]
                    #must be at the same level of the previous partial match
                    if ctx.uid != sub_ctx.uid[:-1]:
                        log("NOT AT THE LEVEL %s ?? %s" % (ctx.uid, sub_ctx.uid[:-1]))
                        sub_ctx.reset_tree()
                    else:
                        ctx.nbsuccess += 1
            # I don't have finish
            log("CHECK MATCHING %d: %s & nbsuccess %d & nbrunning %d" % (id(ctx), ctx.matching, ctx.nbsuccess, ctx.nbrunning))
            # on a partial match, resync the failed
            #if ctx.matching or ctx.nbrunning or ctx.nbsuccess:
            if ctx.nbrunning or ctx.nbsuccess:
                log("Need TO RESET")
                for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                    if sub_ctx.res == State.FAILED:
                        log("RESET %d" % id(sub_ctx))
                        # reset
                        sub_ctx.reset_tree()
                return ctx.set_res(State.RUNNING)
            log("FAILED TO RESET")
            return ctx.set_res(State.FAILED)

    def do_down_template(self, t, data, ctx, user_data):
        ctx.init_state(self)
        log("%s %s" % (t.upper(), ctx.state))
        if ctx.state == 'enter':
            ctx.state = t
            ctx.init_subs(self.subs)
        if ctx.state == t:
            log("COMPONENT %s: [%s]" % (t, data))
            # calcul if we could begin
            if t == data[Pos.TYPE]:
                # strict
                if self.strict and len(self.subs) != len(data[Pos.ARG]):
                    return ctx.set_res(State.FAILED)
                ctx.uid = data[Pos.UID]
                ctx.state = 'final'
                ctx.nbsuccess = set()
                log("Match %s" % t.upper())
                return ctx.set_res(State.RUNNING)
            return ctx.set_res(State.FAILED)
        if ctx.state == 'final':
            # // match
            ctx.nbrunning = 0
            for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                # tick only running BT
                if sub_ctx.res == State.RUNNING:
                    res = sub_bt.do_down(data, sub_ctx, user_data)
                # count after tick
                if sub_ctx.res == State.RUNNING:
                    ctx.nbrunning += 1
                # partial match
                if sub_ctx.res == State.SUCCESS:
                    ctx.nbsuccess |= {id(sub_ctx)}
            log("RUNNING/NBSUCCESS %s - %s" % (ctx.nbrunning, ctx.nbsuccess))
            if ctx.nbrunning or len(ctx.nbsuccess) != len(self.subs):
                log("GLUUUUU %s - %s" % (ctx.nbrunning, ctx.nbsuccess))
                for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                    if sub_ctx.res == State.FAILED:
                        log("RESET %d" % id(sub_ctx))
                        # reset
                        sub_ctx.reset_tree()
                return ctx.set_res(State.RUNNING)
            if len(ctx.nbsuccess) == len(self.subs):
                return ctx.set_res(State.SUCCESS)
############

class Capture(Pair):
    def do_up(self, data, ctx, user_data) -> State:
        root = ctx.getroot()
        root.init_capture()
        ctx.init_second()
        log("CAPTURE SECOND %d" % id(ctx.second))
        res = self.second.do_up(data, ctx.second, user_data)
        log("CAPTURE RES: %s ID %d" % (res, id(ctx.second)))
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("CAPTURE %s" % self.first)
        root.capture[self.first] = data[Pos.ARG]
        return ctx.set_res(State.SUCCESS)

    def do_down(self, data, ctx, user_data) -> State:
        root = ctx.getroot()
        root.init_capture()
        ctx.init_second()
        log("CAPTURE SECOND %d" % id(ctx.second))
        res = self.second.do_down(data, ctx.second, user_data)
        log("CAPTURE RES: %s ID %d" % (res, id(ctx.second)))
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("CAPTURE %s" % self.first)
        root.capture[self.first] = data[Pos.ARG]
        return ctx.set_res(State.SUCCESS)

class Hook(Pair):
    def do_up(self, data, ctx, user_data) -> State:
        root = ctx.getroot()
        root.init_capture()
        ctx.init_second()
        res = self.second.do_up(data, ctx.second, user_data)
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("HOOK %s" % self.first)
        ## hook must return if a modification was done in the hook -> fixpoint
        if self.first(root.capture, user_data):
            root.nb_modif += 1
        return ctx.set_res(State.SUCCESS)

class Event(Pair):
    def do_up(self, data, ctx, user_data) -> State:
        root = ctx.getroot()
        root.init_event()
        ctx.init_second()
        res = self.second.do_up(data, ctx.second, user_data)
        if res != State.SUCCESS:
            return ctx.set_res(res)
        log("EVENT %s" % self.first)
        root.event |= {self.first}
        return ctx.set_res(State.SUCCESS)

############

class AnyDict(BTItem):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYDICT %s" % ctx.state)
        if ctx.state == 'enter':
            if 'dict' == data[Pos.TYPE]:
                log("ANYDICT SUCCESS ID %d" % (id(ctx)))
                ctx.uid = data[Pos.UID] #!!!!!
                return ctx.set_res(State.SUCCESS)
        return ctx.set_res(State.FAILED)

class Dict(Component, AnyDict):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do_up(self, data, ctx, user_data) -> State:
        return self.do_up_template('dict', data, ctx, user_data)

    def do_down(self, data, ctx, user_data) -> State:
        return self.do_down_template('dict', data, ctx, user_data)

class AnyKey(Expr):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYKEY %s" % ctx.state)
        if ctx.state == 'enter':
            if self.expr:
                ctx.init_second()
                if ctx.second.res != State.SUCCESS:
                    res = self.expr.do_up(data, ctx.second, user_data)
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

class Key(Pair, AnyKey):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("KEY %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do_up(data, ctx.second, user_data)
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

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("KEY %s" % ctx.state)
        if ctx.state == 'enter':
            if 'key' == data[Pos.TYPE] and data[Pos.ARG] == self.first:
                log("Match Key %r" % self.first)
                ctx.uid = data[Pos.UID] #!!!!
                ctx.state = 'key'
                return ctx.set_res(State.RUNNING)
            log("KEY FAILED")
            return ctx.set_res(State.FAILED)
        if ctx.state == 'key':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do_down(data, ctx.second, user_data)
                return ctx.set_res(res)
            return ctx.set_res(State.FAILED)

############

class AnyList(BTItem):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYLIST %s" % ctx.state)
        if ctx.state == 'enter':
            if 'list' == data[Pos.TYPE]:
                log("ANYLIST SUCCESS ID %d" % (id(ctx)))
                ctx.uid = data[Pos.UID]
                return ctx.set_res(State.SUCCESS)
        # I don't have finish
        return ctx.set_res(State.FAILED)

class List(Component, AnyList):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do_up(self, data, ctx, user_data) -> State:
        return self.do_up_template('list', data, ctx, user_data)

    def do_down(self, data, ctx, user_data) -> State:
        return self.do_down_template('list', data, ctx, user_data)

class AnyIdx(Expr):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYIDX %s" % ctx.state)
        if ctx.state == 'enter':
            if self.expr:
                ctx.init_second()
                if ctx.second.res != State.SUCCESS:
                    res = self.expr.do_up(data, ctx.second, user_data)
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

class Idx(Pair, AnyIdx):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("IDX %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do_up(data, ctx.second, user_data)
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

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("IDX %s" % ctx.state)
        if ctx.state == 'enter':
            if 'idx' == data[Pos.TYPE] and data[Pos.ARG] == self.first:
                log("Match Idx %r" % self.first)
                ctx.uid = data[Pos.UID] #!!!!!!!
                ctx.state = 'idx'
                return ctx.set_res(State.RUNNING)
            log("IDX FAILED")
            return ctx.set_res(State.FAILED)
        if ctx.state == 'idx':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do_down(data, ctx.second, user_data)
                return ctx.set_res(res)
            return ctx.set_res(State.FAILED)

############

class AnyAttrs(Component):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYATTRS %s" % ctx.state)
        if ctx.state == 'enter':
            if 'attrs' == data[Pos.TYPE]:
                log("ANYATTRS SUCCESS ID %d" % (id(ctx)))
                ctx.uid = data[Pos.UID]
                return ctx.set_res(State.SUCCESS)
        # I don't have finish
        return ctx.set_res(State.FAILED)

class Attrs(Component):
    def __init__(self, *subs, strict=True):
        Component.__init__(self, *subs)
        self.strict = strict

    def do_up(self, data, ctx, user_data) -> State:
        return self.do_up_template('attrs', data, ctx, user_data)

    def do_down(self, data, ctx, user_data) -> State:
        return self.do_down_template('attrs', data, ctx, user_data)

class AnyAttr(Expr):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYATTR %s" % ctx.state)
        if ctx.state == 'enter':
            if self.expr:
                ctx.init_second()
                if ctx.second.res != State.SUCCESS:
                    res = self.expr.do_up(data, ctx.second, user_data)
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

class Attr(Pair, AnyAttr):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ATTR %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do_up(data, ctx.second, user_data)
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

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ATTR %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.init_second()
            if 'attr' == data[Pos.TYPE] and data[Pos.ARG] == self.first:
                log("Match Attr %r" % self.first)
                ctx.matched = self.first
                ctx.uid = data[Pos.UID] #!!!!
                ctx.when = data[Pos.ARG]
                ctx.state = 'attr'
                return ctx.set_res(State.RUNNING)
            log("ATTR FAILED")
            return ctx.set_res(State.FAILED)
        if ctx.state == 'attr':
            if ctx.second.res != State.SUCCESS:
                res = self.second.do_down(data, ctx.second, user_data)
                return ctx.set_res(res)

############

class AnyValue(BTItem):
    def do_up(self, data, ctx, user_data) -> State:
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

    def do_down(self, data, ctx, user_data) -> State:
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

class Value(Expr, AnyValue):
    def do_up(self, data, ctx, user_data) -> State:
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

    def do_down(self, data, ctx, user_data) -> State:
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
############

class AnyType(Expr):
    def do_up(self, data, ctx, user_data) -> State:
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
            res = self.expr.do_up(data, ctx.second, user_data)
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

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("ANYTYPE %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            log("anytype %s" % type(data[Pos.ARG]))
            if 'type' == data[0]:
                log("Match AnyType")
                ctx.uid = data[Pos.UID]
                ctx.when = type(data[Pos.ARG])
                if self.expr:
                    ctx.state = 'sub'
                    return ctx.set_res(State.RUNNING)
                return ctx.set_res(State.SUCCESS)
            log("ANYTYPE FAILED")
            return ctx.set_res(State.FAILED)
        if ctx.state == 'sub':
            ctx.init_second()
            res = self.expr.do_down(data, ctx.second, user_data)
            return ctx.set_res(res)

class Type(Pair, AnyType):
    def __init__(self, *subs, kindof=False):
        if len(subs) not in [1, 2, 3, 4]:
            raise TypeError("Type take at least one argument at most four argument")
        self.first = subs[0]
        self.steps = []
        self.kindof = kindof
        if len(subs) > 1:
            self.steps.append(subs[1])
        if len(subs) > 2:
            # second must be List or Dict
            self.steps.append(subs[2])
            if not sum(map(lambda _: issubclass(type(self.steps[0]), _), {AnyDict, AnyList})):
                raise TypeError("Second argument must be AnyDict or AnyList not %s" % type(self.steps[0]).__name__)
        if len(subs) > 3:
            # second and thirsd must be List or Dict
            self.steps.append(subs[3])
            if not sum(map(lambda _: issubclass(type(self.steps[1]), _), {AnyDict, AnyList})):
                raise TypeError("Third argument must be AnyDict or AnyList not %s" % type(self.steps[1]).__name__)

    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("TYPE %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            if self.steps:
                ctx.state = 'concurrent'
            else:
                ctx.state = 'final'
            log("TYPE CHANGE TYPE %s" % ctx.state)
        if ctx.state == 'concurrent':
            # todo: 2,3,4
            log("INIT STEPS")
            ctx.init_steps(self)
            # each ctx.steps[X].res in set inside the do thru the callee ctx.set_res
            if len(ctx.steps) == 1:
                if ctx.steps[0].res != State.SUCCESS:
                    log("TRY FIRST")
                    res = self.steps[0].do_up(data, ctx.steps[0], user_data)
                    log("FIRST %s" % res)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
                log("SUCCESS FIRST")
                ctx.state = 'final'
                return ctx.set_res(State.RUNNING)
            elif len(ctx.steps) == 2:
                if ctx.steps[0].res != State.SUCCESS:
                    log("TRY PAIR")
                    res = self.steps[0].do_up(data, ctx.steps[0], user_data)
                    log("PAIR %s" % ctx.steps[0].res)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
                    return ctx.set_res(State.RUNNING)
                log("PAIR SECOND %s" % ctx.steps[0].res)
                if ctx.steps[1].res != State.SUCCESS:
                    res = self.steps[1].do_up(data, ctx.steps[1], user_data)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
                log("PAIR SET TO FINAL")
                ctx.state = 'final'
                return ctx.set_res(State.RUNNING)
            elif len(ctx.steps) == 3:
                log("HERE COME STEP3")
                # concurrent match on the 2 first
                subls = list(map(lambda _: _.res, ctx.steps))[0:2]
                log("SUBLS %s" % subls)
                if subls != [State.SUCCESS, State.FAILED] and subls != [State.FAILED, State.SUCCESS]:
                    for idx, child in list(enumerate(ctx.steps))[0:2]:
                        log("PING %d" % idx)
                        res = self.steps[idx].do_up(data, child, user_data)
                    subls = list(map(lambda _: _.res, ctx.steps))[0:2]
                    log("SUBLS2 %s" % subls)
                    if subls == [State.FAILED, State.FAILED]:
                        log("2FAILED")
                        return ctx.set_res(State.FAILED)
                    # still RUNNING if matched or subpart RUNNING
                    log("1RUNNING")
                    return ctx.set_res(State.RUNNING)
                log("STEP3 %s" % ctx.steps[2].res)
                if ctx.steps[2].res != State.SUCCESS:
                    log("DO STEP3")
                    res = self.steps[2].do_up(data, ctx.steps[2], user_data)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
                log("STEP3 FINAL")
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

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("TYPE %s" % ctx.state)
        ### Au début
        if ctx.state == 'enter':
            log("%s ?? %s" % (type(data[Pos.ARG]).__name__, type(self.first).__name__))
            cmp_type = type(data[Pos.ARG]) is self.first
            if self.kindof:
                cmp_type = issubclass(type(data[Pos.ARG]), self.first)
            if 'type' == data[0] and cmp_type:
                log("D Match Type %r" % self.first)
                ctx.uid = data[Pos.UID]
                ctx.when = type(data[Pos.ARG]).__name__
                if not self.steps:
                    return ctx.set_res(State.SUCCESS)
                ### SUITE
                ctx.state = 'concurrent'
                log("D TYPE RUNNING")
                return ctx.set_res(State.RUNNING)
            return ctx.set_res(State.FAILED)
        if ctx.state == 'concurrent':
            # todo: 2,3,4
            log("D INIT STEPS")
            ctx.init_steps(self)
            # each ctx.steps[X].res in set inside the do thru the callee ctx.set_res
            if len(ctx.steps) == 1:
                if ctx.steps[0].res != State.SUCCESS:
                    log("D TRY FIRST")
                    self.steps[0].do_down(data, ctx.steps[0], user_data)
                return ctx.set_res(ctx.steps[0].res)
            elif len(ctx.steps) == 2:
                if ctx.steps[0].res != State.SUCCESS:
                    log("D TRY PAIR")
                    res = self.steps[0].do_down(data, ctx.steps[0], user_data)
                    log("D PAIR %s" % ctx.steps[0].res)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
                    return ctx.set_res(State.RUNNING)
                log("D PAIR SECOND %s" % ctx.steps[0].res)
                if ctx.steps[1].res != State.SUCCESS:
                    self.steps[1].do_down(data, ctx.steps[1], user_data)
                return ctx.set_res(ctx.steps[1].res)
            elif len(ctx.steps) == 3:
                log("D HERE COME STEP3")
                # concurrent match on the 2 first
                subls = list(map(lambda _: _.res, ctx.steps))[0:2]
                log("D SUBLS %s" % subls)
                if subls != [State.SUCCESS, State.FAILED] and subls != [State.FAILED, State.SUCCESS]:
                    for idx, child in list(enumerate(ctx.steps))[0:2]:
                        log("D PING %d" % idx)
                        res = self.steps[idx].do_down(data, child, user_data)
                    subls = list(map(lambda _: _.res, ctx.steps))[0:2]
                    log("D SUBLS2 %s" % subls)
                    if subls == [State.FAILED, State.FAILED]:
                        log("D 2FAILED")
                        return ctx.set_res(State.FAILED)
                    # still RUNNING if matched or subpart RUNNING
                    log("D 1RUNNING")
                    return ctx.set_res(State.RUNNING)
                log("D STEP3 %s" % ctx.steps[2].res)
                if ctx.steps[2].res != State.SUCCESS:
                    log("D DO STEP3")
                    self.steps[2].do_down(data, ctx.steps[2], user_data)
                return ctx.set_res(ctx.steps[2].res)

def KindOf(*subs):
    res = Type(*subs, kindof=True)
    return res

############

class Ancestor(Pair):
    def __init__(self, first, second, depth=1, strict=True):
        """
            strict means that the depth between the ancestor and the child is exactly at depth
            otherwise it's greater than or equal
        """
        Pair.__init__(self, first, second)
        self.depth = depth
        self.strict = strict

    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        ctx.init_first()
        ctx.init_second()
        log("Ancestor %s" % ctx.state)
        if ctx.state == 'enter':
            res = self.second.do_up(data, ctx.second, user_data)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            log("Ancestor Found Child")
            ctx.state = 'final'
            ctx.uid = data[Pos.UID]
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'final':
            log("Ancestor begin search")
            res = self.first.do_up(data, ctx.first, user_data)
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

    def do_up(self, data, ctx, user_data) -> State:
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
                    res = sub_bt.do_up(data, sub_ctx, user_data)
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
