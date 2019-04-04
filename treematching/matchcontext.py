"""
    MatchContext...

    Objects for handles states during pattern matching...
"""

from enum import IntEnum
from treematching.debug import *

class State(IntEnum):
    FAILED = 0
    SUCCESS = 1
    RUNNING = 2

class Pos(IntEnum):
    TYPE = 0
    ARG = 1
    UID = 3


class MatchContext:
    def __init__(self):
        self.res = State.RUNNING
        self.parent = None

    def getroot(self):
        curr = self
        r = self.parent
        while r != None:
            curr = r
            r = r.parent
        return curr

    def getcomponent(self):
        r = self.parent
        if r is None:
            return self
        while True:
            if hasattr(r, 'matching'):
                return r
            if r.parent is not None:
                r = r.parent
            else:
                return r

    def set_res(self, r):
        log("SET RES %d TO %s" % (id(self), r))
        self.res = r
        component = self.getcomponent()
        log("SET RES Match %s in upper component %d" % (r, id(component)))
        if r == State.SUCCESS:
            component.matching = True
            log("SET!!!! on %d" % id(component))
        return r

    def __repr__(self) -> str:
        d = vars(self)
        txt = "\n".join(["\n%s: %s" % (k, v) for k, v in d.items()])
        return txt

    def init_capture(self):
        if not hasattr(self, 'capture'):
            log("create capture")
            self.capture = {}
            # for searching fixpoint
            self.nb_modif = 0

    def init_event(self):
        if not hasattr(self, 'event'):
            log("create event")
            self.event = set()
            self.to_del_event = set()

    def init_state(self, oth):
        if not hasattr(self, 'type'):
            log("create type")
            self.type = type(oth).__name__
            self.state = 'enter'

    def init_first(self):
        """
            mimic first of Pair
        """
        if not hasattr(self, 'first'):
            log("create first")
            self.first = MatchContext()
            # connect to parent
            self.first.parent = self

    def init_second(self):
        """
            mimic second of Expr/Pair
        """
        if not hasattr(self, 'second'):
            log("create second")
            self.second = MatchContext()
            # connect to parent
            self.second.parent = self

    def init_steps(self, btitem):
        """
            2, 3, 4 steps
        """
        # use self.steps....
        if not hasattr(self, 'steps'):
            self.steps = []
        log("LEN steps %s" % len(btitem.steps))
        if len(btitem.steps) >= 1 and len(self.steps) < 1:
            log("steps second")
            self.steps.append(MatchContext())
            # connect to parent
            self.steps[0].parent = self
        if len(btitem.steps) >= 2 and len(self.steps) < 2:
            log("steps third")
            self.steps.append(MatchContext())
            # connect to parent
            self.steps[1].parent = self
        if len(btitem.steps) >= 3 and len(self.steps) < 3:
            log("steps four")
            self.steps.append(MatchContext())
            # connect to parent
            self.steps[2].parent = self

    def init_subs(self, l):
        """
            mimic subs of Component
        """
        if not hasattr(self, 'subs'):
            self.idx = 0
            self.maxidx = len(l)
            self.subs = []
            for i in range(self.maxidx):
                s = MatchContext()
                # connect to parent
                s.parent = self
                self.subs.append(s)

    def reset_tree(self):
        self.state = 'enter'
        self.res = State.RUNNING
        if hasattr(self, 'first'):
            self.first.reset_tree()
        if hasattr(self, 'second'):
            self.second.reset_tree()
        if hasattr(self, 'steps'):
            for s in self.steps:
                s.reset_tree()
        if hasattr(self, 'subs'):
            for s in self.subs:
                s.reset_tree()
