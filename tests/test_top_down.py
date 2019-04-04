import unittest

from treematching.matchingbtree import *
from treematching.btitems import *
from treematching.debug import *

class Dummy:
    def __init__(self, **kw):
        self.__dict__.update(kw)

class DummyList(list):
    def __init__(self, l, **kw):
        if type(l) is not list:
            raise TypeError("Take a list not %s" % repr(type(l)))
        self.extend(l)
        self.__dict__.update(kw)

class DummyDict(dict):
    def __init__(self, d, **kw):
        if type(d) is not dict:
            raise TypeError("Take a dict not %s" % repr(type(d)))
        self.update(d)
        self.__dict__.update(kw)

class A(Dummy): pass
class B(Dummy): pass
class C(Dummy): pass
class D(Dummy): pass
class E(Dummy): pass
class AL(DummyList): pass
class BL(DummyList): pass
class CL(DummyList): pass
class DL(DummyList): pass
class EL(DummyList): pass
class AD(DummyDict): pass
class BD(DummyDict): pass
class CD(DummyDict): pass
class DD(DummyDict): pass
class ED(DummyDict): pass

class TestTopDown(unittest.TestCase):
    def test_01(self):
        """
        literal subtree with Type, Attrs, Attr, Value, AnyType, AnyValue
        """
        bt = Type(A,
                    Attrs(
                        Attr('a', Type(int, Value(32))),
                        Attr('b', Type(str, Value('toto'))),
                        Attr('c', Type(str, Value('lala')))
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = A(a=32, b='toto', c='lala')
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match a basic tree")
        tree = [B(a=32, b='toto', c='lala'), A(a=32, b='toto', c='lala')]
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match a basic tree")
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=A(a=32, b='toto', c='lala')), A(a=32, b='toto', c='lala', d=12)]}
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match a basic tree")
        bt = Type(A,
                    Attrs(
                        Attr('a', AnyType(AnyValue())),
                        Attr('b', AnyType(AnyValue())),
                        Attr('c', AnyType(AnyValue()))
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = A(a=3.2, b=b'toto', c=b'lala')
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match a basic tree")
        tree = [B(a=32, b='toto', c='lala'), A(a=32, b='toto', c='lala')]
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match a basic tree")
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=A(a=32, b='toto', c='lala')), A(a=32, b='toto', c='lala', d=12)]}
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match a basic tree")

    def test_02(self):
        """
        unordered attrs
        """
        bt = Type(A,
                    Attrs(
                        Attr('c', Type(str, Value('lala'))),
                        Attr('b', Type(str, Value('toto'))),
                        Attr('a', Type(int, Value(32))),
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = A(a=32, b='toto', c='lala')
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unordered tree")
        tree = [B(a=32, b='toto', c='lala'), A(a=32, b='toto', c='lala')]
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unordered tree")
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=A(a=32, b='toto', c='lala'))]}
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unordered tree")
        # stricly empty
        bt = Type(A)
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=A()), A(a=32, b='toto', c='lala', d=12)]}
        match = e.match(tree)
        # TODO: 1 -> 2
        self.assertEqual(len(match), 2, "Failed to match an empty strict attrs")

    def test_03(self):
        """
        not strict attrs
        """
        bt = Type(A,
                    Attrs(
                        Attr('g', Type(str, Value('lala'))),
                        Attr('f', Type(str, Value('toto'))),
                        Attr('e', Type(int, Value(32))),
                        strict=False
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [B(e=32, f='toto', g='lala'), C(v=A(e=32, f='toto', g='lala', a=13)), A(e=32, f='toto', g='lala', d=12, a=15)]}
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict attrs")
        tree = {A(e=32, f='toto', g='lala', d=A(e=32, f='toto', g='lala', d=A(e=32, f='toto', g='lala', a=16))), A()}
        match = e.match(tree)
        # TODO: top/down see only 1
        self.assertEqual(len(match), 1, "Failed to match an unstrict attrs")
        # empty
        bt = Capture('a', Type(A))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=A(a=32, b='toto', c='lala')), A(a=32, b='toto', c='lala', d=12)]}
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict attrs")

    def test_04(self):
        """
        list
        """
        bt = Type(AL,
                    List(
                        Idx(2, Type(str, Value('lala'))),
                        Idx(1, Type(str, Value('toto'))),
                        Idx(0, Type(int, Value(32))),
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = AL([32, 'toto', 'lala'])
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unordered tree")
        tree = [B(a=32, b='toto', c='lala'), AL([32, 'toto', 'lala'])]
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unordered tree")
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=AL([32, 'toto', 'lala'])), AL([32, 'toto', 'lala', 'lili'])]}
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unordered tree")

    def test_05(self):
        """
        dict
        """
        bt = Type(AD,
                    Dict(
                        Key('c', Type(str, Value('lala'))),
                        Key('b', Type(str, Value('toto'))),
                        Key('a', Type(int, Value(32))),
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = AD({'a':32, 'b':'toto', 'c':'lala'})
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unordered tree")
        tree = [B(a=32, b='toto', c='lala'), AD({'a':32, 'b':'toto', 'c':'lala'})]
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unordered tree")
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=AD({'a': 32, 'b': 'toto', 'c': 'lala'})), AD({'a': 32, 'b': 'toto', 'c': 'lala', 'd': 42})]}
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unordered tree")

    def test_06(self):
        """
        list non strict
        """
        bt = Type(AL,
                    List(
                        Idx(2, Type(str, Value('lala'))),
                        Idx(1, Type(str, Value('toto'))),
                        Idx(0, Type(int, Value(32))),
                        strict=False
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = AL([32, 'toto', 'lala', 12, 'pouet'])
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unstrict list")
        tree = [B(a=32, b='toto', c='lala'), AL([32, 'toto', 'lala', 'lili'])]
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unstrict list")
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=AL([32, 'toto', 'lala'])), AL([32, 'toto', 'lala', 'lili'])]}
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict list")
        tree = AL([32, 'toto', 'lala', 666, AL([32, 'toto', 'lala', AL([32, 'toto', 'lala'])])])
        match = e.match(tree)
        self.assertEqual(len(match), 3, "Failed to match an unstrict list")
        # empty
        bt = Type(AL, List(AnyIdx(), strict=False))
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=AL([32, 'toto', 'lala'])), AL([32, 'toto', 'lala', 'lili'])]}
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict list")

    def test_07(self):
        """
        dict non strict
        """
        bt = Type(AD,
                    Dict(
                        Key('c', Type(str, Value('lala'))),
                        Key('b', Type(str, Value('toto'))),
                        Key('a', Type(int, Value(32))),
                        strict=False
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = AD({'a':32, 'b':'toto', 'c':'lala', 'k': 43})
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unstrict dict")
        tree = [B(a=32, b='toto', c='lala'), AD({'a':32, 'b':'toto', 'c':'lala', 'g': 12})]
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unstrict dict")
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=AD({'a': 32, 'b': 'toto', 'c': 'lala'})), AD({'a': 32, 'b': 'toto', 'c': 'lala', 'd': 42})]}
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict dict")
        tree = AD({'a': 32, 'b': 'toto', 'c': 'lala', 'r': AD({'a': 32, 'b': 'toto', 'c': 'lala', 'r': AD({'a': 32, 'b': 'toto', 'c': 'lala'})})})
        match = e.match(tree)
        self.assertEqual(len(match), 3, "Failed to match an unstrict dict")
        # empty
        bt = Type(AD, Dict(AnyKey(), strict=False))
        tree = {'cool': [B(a=32, b='toto', c='lala'), AD({}), C(v=AD({'a': 32, 'b': 'toto', 'c': 'lala'})),
                AD({'a': 32, 'b': 'toto', 'c': 'lala', 'd': 42})]}
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict dict")

    def test_08(self):
        """
        strict attrs with anyattr
        """
        bt = Type(A,
                    Attrs(
                        AnyAttr(Type(str, Value('lala'))),
                        AnyAttr(Type(str, Value('toto'))),
                        AnyAttr(Type(int, Value(32))),
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=A(a=32, b='toto', c='lala')), A(k=32, z='toto', t='lala', d=12)],
            'plum': A(g='lala', z=32, l='toto')
            }
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict attrs")
        bt = Type(A,
                    Attrs(
                        AnyAttr(Type(str, Value('lala'))),
                        AnyAttr(Type(str, Value('toto'))),
                        Attr('a', Type(int, Value(32))),
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=A(a=32, b='toto', c='lala')), A(k=32, z='toto', t='lala', d=12)],
            'plum': A(g='lala', z=32, l='toto')
            }
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unstrict attrs")
        bt = Type(A,
                    Attrs(
                        AnyAttr(Type(str, Value('lala'))),
                        AnyAttr(Type(str, Value('toto'))),
                        Attr('a', Type(int, Value(32))),
                        strict=False
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=A(a=32, b='toto', c='lala')), A(k=32, z='toto', t='lala', d=12)],
            'plum': A(g='lala', a=32, l='toto', bol='riz')
            }
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict attrs")

    def test_09(self):
        """
        strict list with anyattr
        """
        bt = Type(AL,
                    List(
                        AnyIdx(Type(str, Value('lala'))),
                        AnyIdx(Type(str, Value('toto'))),
                        AnyIdx(Type(int, Value(32))),
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=AL([32, 'toto', 'lala'])), AL([32, 'toto', 'lala', 12])],
            'plum': AL(['lala', 32, 'toto'])
            }
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict attrs")
        bt = Type(AL,
                    List(
                        AnyIdx(Type(str, Value('lala'))),
                        AnyIdx(Type(str, Value('toto'))),
                        Idx(0, Type(int, Value(32))),
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=AL([32, 'lala', 'toto'])), AL([32, 'toto', 'lala', 12])],
            'plum': AL(['lala', 32, 'toto'])
            }
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unstrict attrs")
        bt = Type(AL,
                    List(
                        AnyIdx(Type(str, Value('lala'))),
                        AnyIdx(Type(str, Value('toto'))),
                        Idx(0, Type(int, Value(32))),
                        strict=False
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [B(a=32, b='toto', c='lala'), C(v=AL([32, 'toto', 'lala'])), AL([32, 'toto', 'lala', 12])],
            'plum': AL(['lala', 32, 'toto'])
            }
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict attrs")

    def test_10(self):
        """
        strict dict with anyattr
        """
        bt = Type(AD,
                    Dict(
                        AnyKey(Type(str, Value('lala'))),
                        AnyKey(Type(str, Value('toto'))),
                        AnyKey(Type(int, Value(32))),
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [BD({'a':32, 'b':'toto', 'c':'lala'}), C(v=AD({'x':32, 'y':'toto', 'z':'lala'})), AD({'x':32, 'y':'toto', 'z':'lala', 'a':12})],
            'plum': AD({'a':'lala', 'b':32, 'c':'toto'})
            }
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict attrs")
        bt = Type(AD,
                    Dict(
                        AnyKey(Type(str, Value('lala'))),
                        AnyKey(Type(str, Value('toto'))),
                        Key('a', Type(int, Value(32))),
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [BD({'a':32, 'b':'toto', 'c':'lala'}), CD({'v':AD({'a':32, 'b':'lala', 'c':'toto'}), 's': None}), AD({'a':32, 'x':'toto', 'e':'lala', 'l':12})],
            'plum': AD({'f':'lala', 'b':32, 'g':'toto'})
            }
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match an unstrict attrs")
        bt = Type(AD,
                    Dict(
                        AnyKey(Type(str, Value('lala'))),
                        AnyKey(Type(str, Value('toto'))),
                        Key('a', Type(int, Value(32))),
                        strict=False
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [
                    BD({'a':32, 'b':'toto', 'c':'lala'}), CD({'v':AD({'a':32, 'b':333, 'c':'lala', 'd':'toto'}), 's': None}),
                    AD({'a':32, 'x':'toto', 'e':'lala', 'l':12})
                ],
            'plum': AD({'f':'lala', 'b':32, 'g':'toto'})
            }
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match an unstrict attrs")

    def test_11(self):
        """
        basic capture
        """
        bt = Capture('a', Type(A))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = [A(), B(), C()]
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match and capture")
        self.assertEqual(id(match[0].capture['a']), id(tree[0]), "Failed to capture correctly")

        bt = Capture('a', Value(32))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = [A(v=44), B(c=32), C(d=1,e=32)]
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match and capture")
        self.assertEqual(id(match[0].capture['a']), id(tree[1].c), "Failed to capture correctly")
        self.assertEqual(id(match[1].capture['a']), id(tree[2].e), "Failed to capture correctly")

        bt = Capture('a', List(AnyIdx(Type(int, Value(32))), strict=False))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = [AL([44, 46, 47]), BL([12, 18, 23, 32]), CL([1, 32]), 12, 42]
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match and capture")
        self.assertEqual(id(match[0].capture['a']), id(tree[1]), "Failed to capture correctly")
        self.assertEqual(id(match[1].capture['a']), id(tree[2]), "Failed to capture correctly")

        bt = Capture('a', Attrs(AnyAttr(Type(int, Value(32))), strict=False))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = [A(a=44, b=46, c=47), B(a=12, b=18, c=23, d=32), C(a=1, b=32), 12, 42]
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match and capture")
        self.assertEqual(id(match[0].capture['a']), id(vars(tree[1])), "Failed to capture correctly")
        self.assertEqual(id(match[1].capture['a']), id(vars(tree[2])), "Failed to capture correctly")

        bt = Capture('a', Dict(AnyKey(Type(int, Value(32))), strict=False))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'a': AD({'a': 44, 'b': 46, 'c': 47}), 'b': BD({'a': 12, 'b': 18, 'c': 23, 'd': 32}), 'c': CD({'a': 1, 'b': 32}), 'd': 12, 'e': 42}
        match = e.match(tree)
        self.assertEqual(len(match), 2, "Failed to match and capture")
        self.assertEqual(id(match[0].capture['a']), id(tree['b']), "Failed to capture correctly")
        self.assertEqual(id(match[1].capture['a']), id(tree['c']), "Failed to capture correctly")

    def test_12(self):
        """
        KindOf

        TODO: Any not super clear
        """
        class Base:
            def __repr__(self) -> str:
                return "%s(%s)" % (type(self).__name__, repr(self.__dict__))
        class Sub1(Base, AL):
            def __repr__(self) -> str:
                return "%s(%s, %s)" % (type(self).__name__, list.__repr__(self), ', '.join(["%s=%s" % (k, repr(v)) for k, v in self.__dict__.items()]))
        class Sub2(Base, AD):
            def __repr__(self) -> str:
                return "%s(%s, %s)" % (type(self).__name__, dict.__repr__(self), ', '.join(["%s=%s" % (k, repr(v)) for k, v in self.__dict__.items()]))
        class Sub3(Base, Dummy):
            pass

        # when we provide only one Attrs, AnyList or AnyDict must failed
        bt = Capture('a', KindOf(Base,
                    Attrs(
                        Attr('flags', AnyType(AnyValue())),
                        strict=False
                    )
            ))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [Sub2({'a':32, 'b':'toto', 'c':'lala'}, blim=None, flags=True), 
                        Sub3(flags=12, grim=False), C(v=AD({'x':32, 'y':'toto', 'z':'lala'})), 
                        Sub1([12, 14, 16], flags='toto', a=12)],
            'plum': AD({'a':'lala', 'b':32, 'c':'toto'})
            }
        match = e.match(tree)
        self.assertEqual(len(match), 1, "Failed to match a KindOf")
        self.assertEqual(match[0].capture['a'].flags, 12, "Failed to match a KindOf")
        self.assertIs(type(match[0].capture['a']), Sub3, "Failed to match a KindOf")

        # TODO: same pb than in bottom-up
        bt = Capture('a', KindOf(Base,
                        #AnyList(),
                        #AnyDict(),
                        Attrs(
                            Attr('flags', AnyType(AnyValue())),
                            strict=False
                        ),
                   )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [Sub2({'a':32, 'b':'toto', 'c':'lala'}, a=None, flags=True),
                        Sub3(flags=12), C(v=AD({'x':32, 'y':'toto', 'z':'lala'})),
                        Sub1([12, 14, 16], a=None, flags='toto')],
            'plum': AD({'a':'lala', 'b':32, 'c':'toto'})
            }
        match = e.match(tree)
        # TODO: 3!
        self.assertEqual(len(match), 1, "Failed to match a KindOf")
        self.assertEqual(match[0].capture['a'].flags, 12, "Failed to match a KindOf")
        self.assertIs(type(match[0].capture['a']), Sub3, "Failed to match a KindOf")
        #self.assertEqual(match[1].capture['a'].flags, 'toto', "Failed to match a KindOf")
        #self.assertIs(type(match[1].capture['a']), Sub1, "Failed to match a KindOf")

        # TODO: Any??
        bt = Capture('a', KindOf(Base,
                        AnyDict(),
                        Attrs(
                            Attr('flags', AnyType(AnyValue())),
                            strict=False
                        )
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [Sub2({'a':32, 'b':'toto', 'c':'lala'}, flags=True, b=13),
                        Sub3(flags=12), C(v=AD({'x':32, 'y':'toto', 'z':'lala'})),
                        Sub1([12, 14, 16], flags='toto', a=12)],
            'plum': AD({'a':'lala', 'b':32, 'c':'toto'})
            }
        match = e.match(tree)
        #self.assertEqual(len(match), 1, "Failed to match a KindOf")
        #self.assertEqual(match[0].capture['a'].flags, True, "Failed to match a KindOf")
        #self.assertIs(type(match[0].capture['a']), Sub2, "Failed to match a KindOf")
        
        bt = Capture('a', KindOf(Base,
                        AnyList(),
                        Attrs(
                            Attr('flags', AnyType(AnyValue())),
                            strict=False
                        )
                    )
            )
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = {'cool': [Sub2({'a':32, 'b':'toto', 'c':'lala'}, flags=True),
                        Sub3(flags=12), C(v=AD({'x':32, 'y':'toto', 'z':'lala'})),
                        Sub1([12, 14, 16], flags='toto', a=12)],
            'plum': AD({'a':'lala', 'b':32, 'c':'toto'})
            }
        match = e.match(tree)
        #self.assertEqual(len(match), 1, "Failed to match a KindOf")
        #self.assertEqual(match[0].capture['a'].flags, 'toto', "Failed to match a KindOf")
        #self.assertIs(type(match[0].capture['a']), Sub1, "Failed to match a KindOf")

    def test_13(self):
        """
        Hook
        """
        def hook_test(capture, user_data):
            user_data.assertTrue(isinstance(capture['a'], A), "Failed to Hook")
            return True

        bt = Hook(hook_test, Capture('a', Type(A)))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = [A(), B(), C()]
        match = e.match(tree, user_data=self)

        def hook_modif(capture, user_data):
            user_data.assertTrue(isinstance(capture['a'], A), "Failed to Hook")
            user_data.assertTrue(isinstance(capture['b'], B), "Failed to Hook")
            user_data.assertEqual(capture['b'].flag, 12, "Failed to Hook")
            capture['a'].chaussette = 'cool'
            todel = []
            for k, v in vars(capture['b']).items():
                setattr(capture['a'], k, v)
                todel.append(k)
            for d in todel:
                delattr(capture['b'], d)
            return True

        bt = Hook(hook_modif, Capture('a', Type(A, Attrs(AnyAttr(Capture('b', Type(B))), strict=False))))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)
        tree = [A(), B(), C(z=A(a=B(flag=12)))]
        match = e.match(tree, self)
        self.assertEqual(len(match), 1, "Failed to Hook")
        self.assertEqual(tree[2].z.chaussette, 'cool', "Failed to Hook")
        self.assertEqual(tree[2].z.flag, 12, "Failed to Hook")
        self.assertTrue(isinstance(tree[2].z.a, B), "Failed to Hook")
        self.assertEqual(len(vars(tree[2].z.a)), 0, "Failed to Hook")

    def test_14(self):
        """
        Ancestor
        """
        def hook_test(capture, user_data):
            user_data.assertTrue(isinstance(capture['a'], A), "Failed to Ancestor")
            return True
        def hook_test2(capture, user_data):
            user_data.assertTrue(isinstance(capture['a'], AL), "Failed to Ancestor")
            return True
        def hook_test3(capture, user_data):
            user_data.assertTrue(isinstance(capture['a'], AD), "Failed to Ancestor")
            return True

        bt = Hook(hook_test, Capture('a', Ancestor(Type(A), Type(B))))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)

        tree = [A(), C(), C(z=A(a=B()))]
        match = e.match(tree, self)
        self.assertEqual(len(match), 1, "Failed to match a Ancestor")

        bt = Hook(hook_test, Capture('a', Ancestor(Type(A), Type(B), 2)))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)

        tree = [A(), C(), C(z=A(a=C(a=B())))]
        match = e.match(tree, self)
        self.assertEqual(len(match), 1, "Failed to match a Ancestor")

        bt = Hook(hook_test, Capture('a', Ancestor(Type(A), Type(B), 3)))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)

        tree = [A(), C(), C(z=A(a=C(z=A(a=B()))))]
        match = e.match(tree, self)
        self.assertEqual(len(match), 1, "Failed to match a Ancestor")

        bt = Hook(hook_test, Capture('a', Ancestor(Type(A), Type(B), 3, strict=False)))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)

        tree = [A(), C(), C(z=A(a=C(g=D(z=A(a=B())))))]
        match = e.match(tree, self)
        self.assertEqual(len(match), 1, "Failed to match a Ancestor")

        bt = Hook(hook_test2, Capture('a', Ancestor(Type(AL), Type(B))))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)

        tree = [A(), C(), C(z=AL([B()]))]
        match = e.match(tree, self)
        self.assertEqual(len(match), 1, "Failed to match a Ancestor")

        bt = Hook(hook_test3, Capture('a', Ancestor(Type(AD), Type(B))))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)

        tree = [A(), C(), C(z=AD({'plop': B()}))]
        match = e.match(tree, self)
        self.assertEqual(len(match), 1, "Failed to match a Ancestor")

    def test_15(self):
        """
        Sibling
        """
        def hook_test(capture, user_data):
            user_data.assertTrue(isinstance(capture['a'], A), "Failed to Sibling")
            user_data.assertTrue(isinstance(capture['b'], B), "Failed to Sibling")
            return True

        bt = Hook(hook_test, Sibling(Capture('a', Type(A)), Capture('b', Type(B))))
        e = MatchingBTree(bt, direction=MatchDirection.TOP_DOWN)

        tree = [A(), B(), C()]
        match = e.match(tree, self)
        self.assertEqual(len(match), 1, "Failed to match a Ancestor")

    # TODO: Event, Condition
