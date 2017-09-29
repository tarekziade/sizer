import asyncio
import sys
from molotov.slave import main as moloslave


def _init_molotov():
    from molotov.api import _SCENARIO, _FIXTURES
    _SCENARIO.clear()
    _FIXTURES.clear()
    asyncio.set_event_loop(asyncio.new_event_loop())


def run_molotov(test_url, deployment_url, test_name):
    _init_molotov()
    print('Running %r on %r' % (test_url, deployment_url))
    # run the molotov test
    args = ['moloslave', test_url, test_name]
    old = list(sys.argv)
    print("Running %r" % ' '.join(args))
    sys.argv = args
    try:
        moloslave()
    except SystemExit:
        pass
    finally:
        sys.argv = old
