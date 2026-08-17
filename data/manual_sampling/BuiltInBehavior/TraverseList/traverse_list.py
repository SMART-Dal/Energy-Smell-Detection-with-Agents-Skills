def traverse_list(l: list):
    return [l[i] * 2 for i in range(len(l))]

import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(40):
    a = traverse_list(lst)
    