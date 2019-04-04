import os
from os import path
import sys
import unittest

# Add parent directory in front of path to import treematching and tests from sources
parent_dir = path.join(path.dirname(__file__), os.pardir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from tests import test_common
from tests import test_bottom_up
from tests import test_top_down

# Test cases in order
test_cases = (
    test_common.TestCommon,
    test_bottom_up.TestBottomUp,
    test_top_down.TestTopDown,
)

def load_tests(loader, standard_tests, pattern):
    loader = unittest.defaultTestLoader
    if test_unit:
        suite = loader.discover(parent_dir)
    else:
        suite = unittest.TestSuite()

    if test_integration:
        for test_case in test_cases:
            tests = loader.loadTestsFromTestCase(test_case)
            suite.addTests(tests)
    return suite

if __name__ == '__main__':
    test_unit, test_integration = False, True
    if 'all' in sys.argv[1:]:
        test_unit = True
        sys.argv.remove('all')
    elif 'unit' in sys.argv[1:]:
        test_integration, test_unit = test_unit, test_integration
        sys.argv.remove('unit')
    unittest.main()
