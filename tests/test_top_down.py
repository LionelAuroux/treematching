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
        self.assertEqual(len(match), 3, "Failed to match an unstrict attrs")
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
        e = MatchingBTree(bt)
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
