"""
    Behavior Tree Items...

    All what you need to construct your patterns...

semantics:
    one:
        - up/down: match one thing SUCCESS/FAILED
        - example: Value

    wrap:
        - down:
            - step1: match the wrap, if wrap thing RUNNING (step2), else SUCCESS
            - step2: match the thing SUCCESS/FAILED
        - up:
            - step1: match the thing FAILED/RUNNING (step2)
            - step2: match the wrap, SUCCESS/FAILED
        - example: Attr, Idx, Key

    component:
        - down:
            - step1: match the wrap, strict or not, isany RUNNING/SUCCESS or FAILED
            - step2: concurrent match:
                        tick only running BT
                        count after tick
                        partial match
                    reset partial match
                    Success on all concurrent match
        - up:
            - step1: check conccurrent match by depth, success
            - step2: conccurrent match:
                        tick only running BT
                        count after tick
                        partial match
                    reset partial match
        - example: Component, Dict, List, Attrs

    - type:
        - down:
            - step1: match the wrap, strict or not, isany RUNNING/SUCCESS or FAILED
            - step2: sequence (one_of (List/Dict), Attrs)
        - up:
            - step1: sequence (one_of (List/Dict), Attrs) 
            - step2: match the wrap, strict or not, isany 
        - example: Type, KindOf


    think about:
            guard sequence:
                remember the depth of the first matched item, check that each item is at the same level
                for Dict, List, Key, Attrs
            one_of:
                match only one of a sequence
            any:
                match any (1 or more) of a sequence
            wrap:
                match a wrap around something
            all:
                match all item of a sequence
            concurrent:
                match in // subitems

TODO: let's think of RESETABLE states
"""

from treematching.matchcontext import *
from treematching.conditions import Condition
from treematching.debug import *

class BTItem:
    """
    Base class for all items of a pattern
    """
    def do_up(self, data, ctx, user_data) -> State:
        raise RuntimeError("%s.do_up must be implemented" % type(self).__name__)

    def do_down(self, data, ctx, user_data) -> State:
        raise RuntimeError("%s.do_down must be implemented" % type(self).__name__)

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
    def __init__(self, expr=None, isany=False):
        self.expr = expr
        self.isany = isany

class Pair(BTItem):
    """
    Pattern that took two argument
    """
    def __init__(self, first=None, second=None, isany=False):
        self.first = first
        self.second = second
        self.isany = isany

class Component(BTItem):
    """
    Pattern that took many argument
    """
    def __init__(self, *subs, strict=True, isany=False):
        self.subs = subs
        self.strict = strict
        self.isany = isany
        if self.isany:
            self.strict = False

    def do_up_template(self, t, data, ctx, user_data):
        ctx.init_state(self)
        # to be notifying by subs
        ctx.matching = False
        log("%s %s" % (t.upper(), ctx.state))
        if ctx.state == 'enter':
            ctx.state = t
            ctx.init_subs(self.subs)
            ctx.nbsuccess = set()
        if ctx.state == t:
            log("COMPONENT %s: [%s]" % (t, data))
            # calcul if we have finish ##
            if t == data[Pos.TYPE] and (not hasattr(ctx, 'uid') or data[Pos.UID] == ctx.uid):
                log("data[UID]: %s" % data[Pos.UID])
                log("LEN: %s ?? %d ?? %d" % (ctx.nbsuccess, len(self.subs), len(data[Pos.ARG])))
                if len(ctx.nbsuccess) == len(self.subs):
                    # strict
                    if self.strict and len(self.subs) != len(data[Pos.ARG]):
                        return ctx.set_res(State.FAILED)
                    log("Match %s" % t.upper())
                    return ctx.set_res(State.SUCCESS)
                # out directly for Any* 
                if self.isany:
                    return ctx.set_res(State.SUCCESS)
                return ctx.set_res(State.FAILED)
            log("check subs")
            # here // match
            ctx.nbrunning = 0
            for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                # tick only running BT
                if sub_ctx.res == State.RUNNING:
                    # deeper function could modify the current ctx.matching
                    log("SUBCTX DOUP %d" % id(sub_ctx))
                    res = sub_bt.do_up(data, sub_ctx, user_data)
                # count after tick
                if sub_ctx.res == State.RUNNING:
                    ctx.nbrunning += 1
                # partial match
                if sub_ctx.res == State.SUCCESS:
                    log("SUBS OK")
                    # take the first uid as ref
                    if not hasattr(ctx, 'uid'):
                        log("SUBCTX %d" % id(sub_ctx))
                        log_json(sub_ctx)
                        ctx.uid = sub_ctx.uid[:-1]
                    #must be at the same level of the previous partial match
                    if ctx.uid != sub_ctx.uid[:-1]:
                        log("NOT AT THE LEVEL %s ?? %s" % (ctx.uid, sub_ctx.uid[:-1]))
                        sub_ctx.reset_tree()
                    else:
                        ctx.nbsuccess |= {id(sub_ctx)}
            # I don't have finish
            log("CHECK MATCHING %d: %s & nbsuccess %s & nbrunning %d" % (id(ctx), ctx.matching, ctx.nbsuccess, ctx.nbrunning))
            # on a partial match, resync the failed
            #if ctx.matching or ctx.nbrunning or ctx.nbsuccess:
            if ctx.nbrunning or len(ctx.nbsuccess):
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
            log("COMPONENT %s: [%s: %s]" % (t, data[Pos.TYPE], data[Pos.ARG]))
            # calcul if we could begin
            if t == data[Pos.TYPE]: ##
                # strict
                if self.strict and len(self.subs) != len(data[Pos.ARG]):
                    return ctx.set_res(State.FAILED)
                ctx.uid = data[Pos.UID]
                if not self.isany:
                    ctx.state = 'final'
                    ctx.nbsuccess = set()
                    log("Match %s" % t.upper())
                    return ctx.set_res(State.RUNNING)
                return ctx.set_res(State.SUCCESS)
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
                if sub_ctx.res == State.SUCCESS and ctx.uid == sub_ctx.uid[:-1]:
                    log("UID CMP %s ?? %s" % (ctx.uid, sub_ctx.uid))
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
                ctx.uid = data[Pos.UID]
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
        ctx.uid = data[Pos.UID]
        return ctx.set_res(State.SUCCESS)

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        root = ctx.getroot()
        if ctx.state == 'enter':
            root.init_capture()
            log("DOWN CAPTURE %s" % self.first)
            root.capture[self.first] = data[Pos.ARG]
            ctx.state = 'final'
        if ctx.state == 'final':
            ctx.init_second()
            log("DOWN CAPTURE SECOND %d" % id(ctx.second))
            res = self.second.do_down(data, ctx.second, user_data)
            log("DOWN CAPTURE RES: %s ID %d" % (res, id(ctx.second)))
            ctx.uid = data[Pos.UID]
            return ctx.set_res(res)

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
        ctx.uid = data[Pos.UID]
        return ctx.set_res(State.SUCCESS)

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        root = ctx.getroot()
        if ctx.state == 'enter':
            root.init_capture()
            ctx.state = 'final'
        if ctx.state == 'final':
            ctx.init_second()
            res = self.second.do_down(data, ctx.second, user_data)
            if res != State.SUCCESS:
                return ctx.set_res(res)
            log("HOOK %s" % self.first)
            ## hook must return if a modification was done in the hook -> fixpoint
            if self.first(root.capture, user_data):
                root.nb_modif += 1
            ctx.uid = data[Pos.UID]
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

class Dict(Component):
    def do_up(self, data, ctx, user_data) -> State:
        return self.do_up_template('dict', data, ctx, user_data)

    def do_down(self, data, ctx, user_data) -> State:
        return self.do_down_template('dict', data, ctx, user_data)

def AnyDict():
    return Dict(isany=True)

############

class Key(Pair):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        if ctx.state == 'enter':
            if self.second:
                ctx.init_second()
                if ctx.second.res != State.SUCCESS:
                    res = self.second.do_up(data, ctx.second, user_data)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
            ctx.state = 'key'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'key':
            if 'key' == data[Pos.TYPE] and (self.isany or data[Pos.ARG] == self.first):
                ctx.uid = data[Pos.UID] #!!!!
                return ctx.set_res(State.SUCCESS)
            return ctx.set_res(State.FAILED)

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        if ctx.state == 'enter':
            if 'key' == data[Pos.TYPE] and (self.isany or data[Pos.ARG] == self.first):
                ctx.uid = data[Pos.UID] #!!!!
                ctx.when = data[Pos.ARG]
                if self.second:
                    ctx.state = 'key'
                    return ctx.set_res(State.RUNNING)
                return ctx.set_res(State.SUCCESS)
            return ctx.set_res(State.FAILED)
        if ctx.state == 'key':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do_down(data, ctx.second, user_data)
                return ctx.set_res(res)
            return ctx.set_res(State.FAILED)

def AnyKey(expr=None):
    return Key(second=expr, isany=True)

############

class List(Component):
    def do_up(self, data, ctx, user_data) -> State:
        return self.do_up_template('list', data, ctx, user_data)

    def do_down(self, data, ctx, user_data) -> State:
        return self.do_down_template('list', data, ctx, user_data)

def AnyList():
    return List(isany=True)

############

class Idx(Pair):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        if ctx.state == 'enter':
            if self.second:
                ctx.init_second()
                if ctx.second.res != State.SUCCESS:
                    res = self.second.do_up(data, ctx.second, user_data)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
            ctx.state = 'idx'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'idx':
            if 'idx' == data[Pos.TYPE] and (self.isany or data[Pos.ARG] == self.first):
                log("IDX===== %d - %s" % (id(ctx), data[Pos.UID]))
                ctx.uid = data[Pos.UID] #!!!!!!!
                ctx.when = data[Pos.ARG]
                return ctx.set_res(State.SUCCESS)
            return ctx.set_res(State.FAILED)

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        if ctx.state == 'enter':
            if 'idx' == data[Pos.TYPE] and (self.isany or data[Pos.ARG] == self.first):
                ctx.uid = data[Pos.UID] #!!!!!!!
                ctx.when = data[Pos.ARG]
                if self.second:
                    ctx.state = 'idx'
                    return ctx.set_res(State.RUNNING)
                ctx.when = data[Pos.ARG]
                return ctx.set_res(State.SUCCESS)
            return ctx.set_res(State.FAILED)
        if ctx.state == 'idx':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do_down(data, ctx.second, user_data)
                if res == State.SUCCESS:
                    ctx.when = data[Pos.ARG]
                    ctx.uid = data[Pos.UID]
                return ctx.set_res(res)
            return ctx.set_res(State.FAILED)

def AnyIdx(expr=None):
    return Idx(second=expr, isany=True)

############

class Attrs(Component):
    def do_up(self, data, ctx, user_data) -> State:
        return self.do_up_template('attrs', data, ctx, user_data)

    def do_down(self, data, ctx, user_data) -> State:
        return self.do_down_template('attrs', data, ctx, user_data)

############

class Attr(Pair):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        if ctx.state == 'enter':
            if self.second:
                ctx.init_second()
                if ctx.second.res != State.SUCCESS:
                    res = self.second.do_up(data, ctx.second, user_data)
                    if res != State.SUCCESS:
                        return ctx.set_res(res)
            ctx.state = 'attr'
            return ctx.set_res(State.RUNNING)
        if ctx.state == 'attr':
            if 'attr' == data[Pos.TYPE] and (self.isany or data[Pos.ARG] == self.first):
                ctx.matched = self.first
                ctx.uid = data[Pos.UID] #!!!!
                ctx.when = data[Pos.ARG]
                return ctx.set_res(State.SUCCESS)
            return ctx.set_res(State.FAILED)

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        if ctx.state == 'enter':
            if 'attr' == data[Pos.TYPE] and (self.isany or data[Pos.ARG] == self.first):
                ctx.matched = self.first
                ctx.uid = data[Pos.UID] #!!!!
                ctx.when = data[Pos.ARG]
                if self.second:
                    ctx.state = 'attr'
                    return ctx.set_res(State.RUNNING)
                return ctx.set_res(State.SUCCESS)
            return ctx.set_res(State.FAILED)
        if ctx.state == 'attr':
            ctx.init_second()
            if ctx.second.res != State.SUCCESS:
                res = self.second.do_down(data, ctx.second, user_data)
                return ctx.set_res(res)
            return ctx.set_res(State.FAILED)

def AnyAttr(expr=None):
    return Attr(second=expr, isany=True)

############

class Value(Expr):
    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        if ctx.state == 'enter':
            if 'value' == data[Pos.TYPE] and (self.isany or data[Pos.ARG] == self.expr):
                ctx.uid = data[Pos.UID]
                ctx.when = data[Pos.ARG]
                return ctx.set_res(State.SUCCESS)
            return ctx.set_res(State.FAILED)

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        if ctx.state == 'enter':
            if 'value' == data[Pos.TYPE] and (self.isany or data[Pos.ARG] == self.expr):
                ctx.uid = data[Pos.UID]
                ctx.when = data[Pos.ARG]
                return ctx.set_res(State.SUCCESS)
            return ctx.set_res(State.FAILED)

def AnyValue(expr=None):
    return Value(expr, isany=True)

############

class Type(Pair):
    def __init__(self, *subs, kindof=False, isanytype=False, isanyattrs=False):
        if len(subs) not in [1, 2, 3, 4]:
            raise TypeError("Type take at least one argument at most four argument")
        self.first = subs[0]
        self.steps = []
        self.kindof = kindof
        self.isanytype = isanytype
        self.isanyattrs = isanyattrs
        if len(subs) > 1:
            self.steps.append(subs[1])
        if len(subs) > 2:
            # second must be List or Dict
            self.steps.append(subs[2])
            if not sum(map(lambda _: issubclass(type(self.steps[0]), _), {Dict, List})):
                raise TypeError("Second argument must be Dict or List not %s" % type(self.steps[0]).__name__)
        if len(subs) > 3:
            # second and thirsd must be List or Dict
            self.steps.append(subs[3])
            if not sum(map(lambda _: issubclass(type(self.steps[1]), _), {Dict, List})):
                raise TypeError("Third argument must be Dict or List not %s" % type(self.steps[1]).__name__)

    def do_up(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        log("TYPE %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.uid = data[Pos.UID]
            if self.steps:
                ctx.state = 'concurrent'
            else:
                if 'type' == data[Pos.TYPE] and not self.isanyattrs and data[Pos.NCHILD] != 0:
                    return ctx.set_res(State.FAILED)
                ctx.state = 'final'
            log("TYPE CHANGE TYPE %s" % ctx.state)
        if ctx.state == 'concurrent':
            # todo: 2,3,4
            log("INIT STEPS")
            ctx.init_steps(self)
            # each ctx.steps[X].res in set inside the node do thru the callee ctx.set_res
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
                nrun = len(list(filter(lambda _: _.res == State.SUCCESS, ctx.steps[0:2])))
                log("NRUN %s" % nrun)
                if nrun != 1:
                    for idx, child in enumerate(ctx.steps[0:2]):
                        if child.res != State.SUCCESS:
                            log("PING %d" % idx)
                            res = self.steps[idx].do_up(data, child, user_data)
                    subls = list(map(lambda _: _.res, ctx.steps[0:2]))
                    log("SUBLS2 %s" % subls)
                    if subls == [State.FAILED, State.FAILED]:
                        log("2FAILED")
                        return ctx.set_res(State.FAILED)
                    # still RUNNING if matched or subpart RUNNING
                    log("ONE SUCCESS CONTINUE")
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
            if not self.isanytype:
                cmp_type = type(data[Pos.ARG]) is self.first
                if self.kindof:
                    cmp_type = issubclass(type(data[Pos.ARG]), self.first)
            if 'type' == data[Pos.TYPE] and (self.isanytype or cmp_type):
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
            if not self.isanytype:
                cmp_type = type(data[Pos.ARG]) is self.first
                if self.kindof:
                    cmp_type = issubclass(type(data[Pos.ARG]), self.first)
            if 'type' == data[0] and (self.isanytype or cmp_type):
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

def AnyType(expr=None):
    return Type(expr, isanytype=True)


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

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        ctx.init_first()
        ctx.init_second()
        log("Ancestor %s" % ctx.state)
        if ctx.state == 'enter':
            log("Ancestor begin search")
            res = self.first.do_down(data, ctx.first, user_data)
            log("Ancestor search %s" % res)
            if res == State.SUCCESS:
                log("TD Ancestor found %s" % res)
                ctx.state = 'final'
                ctx.uid = data[Pos.UID]
                return ctx.set_res(State.RUNNING)
            return ctx.set_res(State.FAILED)
        if ctx.state == 'final':
            # check depth
            new_end = len(ctx.uid)
            res = self.second.do_down(data, ctx.second, user_data)
            if res != State.SUCCESS:
                # wait children
                if ctx.uid == data[Pos.UID][:new_end]:
                    log("Ancestor reset none matching childs")
                    ctx.second.reset_tree()
                    return ctx.set_res(State.RUNNING)
                # it's not a children, failed
                log("Ancestor submatch %s" % res)
                return ctx.set_res(State.FAILED)
            log("Ancestor Found Child")
            log("Ancestor check %s : %s" % (ctx.uid, data[Pos.UID][:new_end]))
            if ctx.uid == data[Pos.UID][:new_end]:
                # strict depth?
                if len(data[Pos.UID]) == new_end + self.depth or (not self.strict and len(data[Pos.UID]) >= new_end + self.depth):
                    return ctx.set_res(State.SUCCESS)
                # too near reset first part
                elif len(data[Pos.UID]) < new_end + self.depth:
                    ctx.second.reset_tree()
                    return ctx.set_res(State.RUNNING)
        return ctx.set_res(State.FAILED)

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
        log("Sibling %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.state = 'subs'
            ctx.init_subs(self.subs)
            ctx.nbsuccess = set()
        if ctx.state == 'subs':
            log("COMPONENT [%s]" % repr(data))
            # here // match
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
                    ctx.nbsuccess |= {id(sub_ctx)}
            # I have finish
            if len(ctx.nbsuccess) == len(self.subs):
                # TODO: need to check uid
                return ctx.set_res(State.SUCCESS)
            # I don't have finish
            log("CHECK SIBLING %d: %s & nbsuccess %s & nbrunning %d" % (id(ctx), ctx.matching, ctx.nbsuccess, ctx.nbrunning))
            # on a partial match, resync the failed
            if ctx.matching or ctx.nbrunning or len(ctx.nbsuccess):
                log("Need TO RESET")
                for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                    if sub_ctx.res == State.FAILED:
                        log("RESET %d" % id(sub_ctx))
                        # reset
                        sub_ctx.reset_tree()
                return ctx.set_res(State.RUNNING)
            return ctx.set_res(State.FAILED)

    def do_down(self, data, ctx, user_data) -> State:
        ctx.init_state(self)
        # to be notifying by subs
        ctx.matching = False
        log("Sibling %s" % ctx.state)
        if ctx.state == 'enter':
            ctx.state = 'subs'
            ctx.init_subs(self.subs)
            ctx.nbsuccess = set()
        if ctx.state == 'subs':
            log("COMPONENT [%s]" % repr(data))
            # here // match
            ctx.nbrunning = 0
            for sub_bt, sub_ctx in zip(self.subs, ctx.subs):
                # tick only running BT
                if sub_ctx.res == State.RUNNING:
                    # deeper function could modify the current ctx.matching
                    res = sub_bt.do_down(data, sub_ctx, user_data)
                # count after tick
                if sub_ctx.res == State.RUNNING:
                    ctx.nbrunning += 1
                if sub_ctx.res == State.SUCCESS:
                    log("SUBS OK")
                    ctx.nbsuccess |= {id(sub_ctx)}
            # I have finish
            if len(ctx.nbsuccess) == len(self.subs):
                # TODO: need to check uid
                return ctx.set_res(State.SUCCESS)
            # I don't have finish
            log("CHECK SIBLING %d: %s & nbsuccess %s & nbrunning %d" % (id(ctx), ctx.matching, ctx.nbsuccess, ctx.nbrunning))
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
