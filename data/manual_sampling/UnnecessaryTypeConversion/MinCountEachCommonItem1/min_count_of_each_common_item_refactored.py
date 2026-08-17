from collections import Counter

def min_count_of_each_common_item(lst1: list, lst2: list):
    res = {}
    occ1 = Counter(lst1)
    occ2 = Counter(lst2)
    for x, v in occ1.items():
        if x in occ2:
            res[x] = min(occ2[x], v)
    return res


import random
random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(100_000)]
lst2 = [random.randint(0, 100) for i in range(100_000)]
for _ in range(10):
    a = min_count_of_each_common_item(lst1, lst2)