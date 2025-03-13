
from collections.abc import Iterable

def dead_and_stretch(v, d):
    # 0 <= d <= 1
    # -1 <= v <= 1 
    if abs(v) < d:
        return 0.0
    else:
        s = 1
        if v < 0:
            s = -1
        return (v - s * d)/(1 - d)

def is_array(ary):
    return isinstance(ary, Iterable) and not isinstance(ary, (str, bytes))

def expand_to_array(item):
    return item if is_array(item) else [item]