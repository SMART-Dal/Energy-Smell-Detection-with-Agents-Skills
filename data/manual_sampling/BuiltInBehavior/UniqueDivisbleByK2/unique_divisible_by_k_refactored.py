def unique_divisible_by_k(lst1: list, k: int):
    set_l1 = set(lst1)
    return {i for i in set_l1 if i % k == 0}


import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(150):
    a = unique_divisible_by_k(lst, 3)