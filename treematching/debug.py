trace = False

import sys
import json

class TreematchEncoder(json.JSONEncoder):
    def __init__(self, *a, **kw):
        kw['indent'] = 2
        return super().__init__(*a, **kw)

    def default(self, obj):
        import treematching.matchcontext as mc
        import treematching.btitems as bt
        if isinstance(obj, mc.MatchContext):
            res = {'id': id(obj), 'parent': id(obj.parent), 'res': repr(obj.res)}
            toremove = ['res', 'parent']
            if hasattr(obj, 'uid'):
                toremove.append('uid')
            if hasattr(obj, 'capture'):
                res['capture'] = obj.capture
                res['nb_modif'] = repr(obj.nb_modif)
                toremove.append('capture')
                toremove.append('nb_modif')
            if hasattr(obj, 'event'):
                res['event'] = obj.event
                res['to_del_event'] = obj.to_del_event
                toremove.append('event')
                toremove.append('to_del_event')
            if hasattr(obj, 'type'):
                res['type'] = obj.type
                res['state'] = repr(obj.state)
                toremove.append('type')
                toremove.append('state')
            attrs = list(vars(obj).keys())
            list(map(attrs.remove, toremove))
            for attr in attrs:
                res[attr] = getattr(obj, attr)
            return res
        if isinstance(obj, bt.BTItem):
            attrs = list(vars(obj).keys())
            res = {'Type': type(obj).__name__}
            for attr in attrs:
                res[attr] = getattr(obj, attr)
            return res
        return {'Type': type(obj).__name__, '__repr__': repr(obj)}

def log_on():
    global trace
    trace = True

def log_off():
    global trace
    trace = False

def log(*t):
    if trace:
       print(*t, flush=True, file=sys.stdout)

def log_json(o):
    log(json.dumps(o, cls=TreematchEncoder))
