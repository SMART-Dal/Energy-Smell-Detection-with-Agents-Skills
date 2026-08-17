import random

def inside_range(low: int, high: int, x: int):
    if x < low:
        return False
    if low <= x <= high:
        return True
    elif x > high:
        return False
    return False

random.seed(123)
tmp1 = random.randint(-1_000_000, 1_000_000)
tmp2 = random.randint(-1_000_000, 1_000_000)
tmp3 = random.randint(-1_000_000, 1_000_000)
for _ in range(50_000_000):
    a = inside_range(tmp1, tmp2, tmp3)
