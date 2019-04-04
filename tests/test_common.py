import unittest

from treematching.matchingbtree import *
from treematching.btitems import *
from treematching.debug import *

class A: pass

class TestCommon(unittest.TestCase):
    def test_00(self):
        """
        Type construction
        """
        # Test Type construction
        with self.assertRaises(TypeError) as exinfo:
            Type(A, Attrs(), List())
        self.assertIn("Second argument", str(exinfo.exception), "Failed to get correct exception message, got %s" % exinfo.exception)
        with self.assertRaises(TypeError) as exinfo:
            Type(A, Attrs(), Dict())
        self.assertIn("Second argument", str(exinfo.exception), "Failed to get correct exception message, got %s" % exinfo.exception)
        with self.assertRaises(TypeError) as exinfo:
            Type(A, List(), Attrs(), List())
        self.assertIn("Third argument", str(exinfo.exception), "Failed to get correct exception message, got %s" % exinfo.exception)
        with self.assertRaises(TypeError) as exinfo:
            Type(A, Dict(), Attrs(), List())
        self.assertIn("Third argument", str(exinfo.exception), "Failed to get correct exception message, got %s" % exinfo.exception)
        with self.assertRaises(TypeError) as exinfo:
            Type(A, Dict(), List(), Attrs(), Attrs())
        self.assertIn("Type take", str(exinfo.exception), "Failed to get correct exception message, got %s" % exinfo.exception)
        # Test Type Concurrent
        bt = Type(A, AnyList(), Attrs())
        ctx = MatchContext()
        ctx.init_state(bt)
        ctx.state = "concurrent"
        bt.do_up(('type', None, None, [0]), ctx, None)
        self.assertEqual(len(ctx.steps), 2, "Failed to correctly initialize steps")
        bt = Type(A, AnyList(), AnyDict(), Attrs())
        ctx = MatchContext()
        ctx.init_state(bt)
        ctx.state = "concurrent"
        bt.do_up(('type', None, None, [0]), ctx, None)
        self.assertEqual(len(ctx.steps), 3, "Failed to correctly initialize steps")
