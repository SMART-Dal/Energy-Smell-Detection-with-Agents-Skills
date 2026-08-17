def merge_list(lst1: list, lst2: list) -> list:
    lst1.extend(lst2)
    return lst1


import random
random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(1_000_000)]
lst2 = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(90):
    a = merge_list(lst1, lst2)
