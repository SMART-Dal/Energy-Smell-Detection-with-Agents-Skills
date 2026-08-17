def traverse_list(l: list):
    return [i * 2 for i in l]

import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(40):
    a = traverse_list(lst)
    