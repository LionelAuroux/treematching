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

    def set_res(self, r):
        self.res = r
        return r

    def __repr__(self) -> str:
        d = vars(self)
        txt = "\n".join(["\n%s: %s" % (k, v) for k, v in d.items()])
        return txt

    def init_capture(self):
        if not hasattr(self, 'capture'):
            log("create capture")
            self.capture = {}

    def init_state(self, oth):
        if not hasattr(self, 'type'):
            log("create type")
            self.type = type(oth).__name__
            self.state = 'enter'

    def init_second(self):
        """
            mimic second of Expr/Pair
        """
        if not hasattr(self, 'second'):
            log("create second")
            self.second = MatchContext()
            # connect to parent
            self.second.parent = self

    def init_subs(self, l):
        """
            mimic subs of Component
        """
        if not hasattr(self, 'subs'):
            self.idx = 0
            self.maxidx = len(l)
            self.subs = []
            for i in range(self.maxidx):
                self.subs.append(MatchContext())
                # connect to parent
                self.subs[-1].parent = self
