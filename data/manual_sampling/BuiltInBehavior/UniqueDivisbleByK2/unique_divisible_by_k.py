def unique_divisible_by_k(lst1: list, k: int):
    return {i for i in lst1 if i % k == 0}


import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(150):
    a = unique_divisible_by_k(lst, 3)