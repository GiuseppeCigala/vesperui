"""Run the VesperUI automated test suite.

Usage:
    python run_tests.py                    # run every widget test
    python run_tests.py -v                 # verbose output
    python run_tests.py test_scrollview    # run a single test module
    python run_tests.py test_button test_slider
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(ROOT, 'tests')


def main(argv):
    if sys.platform != 'win32':
        sys.stderr.write('VesperUI tests require Windows.\n')
        return 1

    os.chdir(ROOT)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    names = [arg for arg in argv[1:] if not arg.startswith('-')]
    verbosity = 2 if '-v' in argv[1:] else 1
    loader = unittest.TestLoader()

    if names:
        modules = ['tests.' + (name[6:] if name.startswith('tests.') else name)
                   for name in names]
        suite = loader.loadTestsFromNames(modules)
    else:
        suite = loader.discover(TESTS, top_level_dir=ROOT)

    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
