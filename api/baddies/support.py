import contextlib
import time


@contextlib.contextmanager
def timing(name=''):
    before = time.perf_counter()
    try:
        yield
    finally:
        after = time.perf_counter()
        t = (after - before) * 1000
        unit = 'ms'
        if t < 100:
            t *= 1000
            unit = 'μs'
        if name:
            name = f' ({name})'
        print(f'> {int(t)} {unit}{name}')
