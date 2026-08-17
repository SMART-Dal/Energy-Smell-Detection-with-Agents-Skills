def merge_data(lst1: list[int], lst2: list[int]):
    res = lst1.copy()
    res.extend(lst2)
    return res


import random

random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(1_000_000)]
lst2 = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(25):
    merge_data(lst1, lst2)