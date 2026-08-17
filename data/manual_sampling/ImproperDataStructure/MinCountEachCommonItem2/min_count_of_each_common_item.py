def min_count_of_each_common_item(lst1: list, lst2: list):
    res = {}
    set1 = set(lst1)
    set2 = set(lst2)
    for x in set1:
        if x in set2:
            res[x] = min(lst1.count(x), lst2.count(x))
    return res


import random
random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(100_000)]
lst2 = [random.randint(0, 100) for i in range(100_000)]
for _ in range(10):
    a = min_count_of_each_common_item(lst1, lst2)