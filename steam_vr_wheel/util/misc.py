
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