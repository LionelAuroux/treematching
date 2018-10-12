"""
    Conditions...

    All what you need to construct event expression for your conditions...
"""

from treematching.matchcontext import MatchContext

class Condition:
    """
    Base class for all condition classes
    """
    def eval(self, ctx: MatchContext) -> bool:
        raise RuntimeError("Must be implemented")

class EventName(Condition):
    """
    Class with one argument
    """
    def __init__(self, name):
        if type(name) is not str:
            raise TypeError("took a str not a %s" % type(name))
        self.name = name

class Expr(Condition):
    """
    Class with one argument
    """
    def __init__(self, expr):
        if not isinstance(expr, (EventName, Expr, Operator)):
            raise TypeError("took a EventName|Expr|Operator not a %s" % type(expr))
        self.expr = expr

class Operator(Condition):
    """
    Class with many argument
    """
    def __init__(self, *subs):
        self.subs = subs

class Has(EventName):
    """
    Check if the event is set in the event set
    """
    def eval(self, ctx: MatchContext) -> bool:
        res = len(ctx.event & {self.name}) == True
        if res:
            ctx.to_del_event |= {self.name}
        return res

class Not(Expr):
    """
    Check if the expr is false
    """
    def eval(self, ctx: MatchContext) -> bool:
        return not self.expr.eval(ctx)

class Or(Operator):
    """
    Apply an Logical OR between each sub-expression
    """
    def eval(self, ctx: MatchContext) -> bool:
        l = []
        for s in self.subs:
            l.append(s.eval(ctx))
        return sum(l) >= 1

class And(Operator):
    """
    Apply an Logical AND between each sub-expression
    """
    def eval(self, ctx: MatchContext) -> bool:
        l = []
        for s in self.subs:
            l.append(s.eval(ctx))
        return sum(l) == len(self.subs)

class Xor(Operator):
    """
    Apply an Logical XOR between each sub-expression
    """
    def eval(self, ctx: MatchContext) -> bool:
        res = None
        for s in self.subs:
            r = s.eval(ctx)
            if res is None:
                res = r
            else:
                res ^= r
        return res
