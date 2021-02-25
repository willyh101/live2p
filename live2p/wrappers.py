import asyncio
import functools
import logging
import time

logger = logging.getLogger('live2p')

def tictoc(func):
    """Prints the runtime of the decorated function."""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        logger.info(f'<{func.__module__}.{func.__name__}> done in {run_time:.3f}s')
        return value
    return wrapper_timer

def run_in_executor(func):
    """Runs a blocking operation from a seperate thread."""
    @functools.wraps(func)
    def wrapper_run_in_executor(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper_run_in_executor
