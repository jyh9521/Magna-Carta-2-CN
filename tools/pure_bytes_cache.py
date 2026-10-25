"""Bounded material reuse for pure byte decoders; never a file/stat cache."""
from collections import OrderedDict
from functools import wraps
from threading import RLock


def bounded_bytes_cache(max_bytes, max_entries=256):
    """Cache exact immutable byte/int arguments, charging both input and output."""
    if (type(max_bytes) is not int or max_bytes <= 0
            or type(max_entries) is not int or max_entries <= 0):
        raise ValueError('positive byte budget required')

    def decorate(function):
        entries = OrderedDict()
        lock = RLock()
        used = 0

        @wraps(function)
        def wrapped(*args, **kwargs):
            nonlocal used
            values = args + tuple(kwargs.values())
            if (len(values) > 16 or any(len(k) > 128 for k in kwargs)
                    or not any(type(v) is bytes for v in values)
                    or any(type(v) not in (bytes, int) for v in values)
                    or any(type(v) is int and not -(1 << 63) <= v < (1 << 63)
                           for v in values)):
                return function(*args, **kwargs)
            key = (args, tuple(sorted(kwargs.items())))
            with lock:
                if key in entries:
                    entries.move_to_end(key)
                    return entries[key][0]
            result = function(*args, **kwargs)
            if type(result) is not bytes:
                return result
            weight = len(result) + sum(len(v) for v in values if type(v) is bytes)
            if weight > max_bytes:
                return result
            with lock:
                if key in entries:
                    entries.move_to_end(key)
                    return entries[key][0]
                while entries and (used + weight > max_bytes or len(entries) >= max_entries):
                    _, (_, removed) = entries.popitem(last=False)
                    used -= removed
                entries[key] = (result, weight)
                used += weight
            return result

        return wrapped
    return decorate
