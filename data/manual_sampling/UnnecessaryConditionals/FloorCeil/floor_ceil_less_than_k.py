import random
import math

def floor_ceil_less_than_k(num: float, k: float):
    floor = math.floor(num)
    ceil = math.ceil(num)
    
    if ceil < k and floor < k:
        return True, True
    if floor < k:
        return False, True
    return False, False

random.seed(123)
tmp1 = random.random() * 1_000_000
tmp2 = random.random() * 1_000_000
for _ in range(80_000_000):
    a = floor_ceil_less_than_k(tmp1, tmp2)
