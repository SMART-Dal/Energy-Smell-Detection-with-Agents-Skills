def min_max_difference(l: list):
    min = l[0]
    max = min
    for x in l:
        if x < min:
            min = x
        elif x > max:
            max = x
    return max - min

import random
random.seed(1234)
lst = [random.randint(0, 10000) for i in range(1_000_000)]
for _ in range(80):
    a = min_max_difference(lst)
