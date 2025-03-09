
import numpy as np

def clamp(x, m, M):
    return min(M, max(m, x))

class Rad(float):
    def __new__(cls, value):
        if isinstance(value, Deg):
            value = value / 180 * np.pi
        return super().__new__(cls, value)

class Deg(float):
    def __new__(cls, value):
        if isinstance(value, Rad):
            value = value / np.pi * 180
        return super().__new__(cls, value)