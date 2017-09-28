import humanize
import time


_STARTED = None


def log(msg):
    global _STARTED
    if _STARTED is None:
        _STARTED = time.time()
    age = humanize.naturaltime(time.time() - _STARTED)
    print("[%s] %s" % (age.capitalize(), msg))
