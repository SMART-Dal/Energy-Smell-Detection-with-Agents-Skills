def min_max_difference(l: list):
    return max(l) - min(l)

import random
random.seed(1234)
lst = [random.randint(0, 10000) for i in range(1_000_000)]
for _ in range(80):
    a = min_max_difference(lst)
