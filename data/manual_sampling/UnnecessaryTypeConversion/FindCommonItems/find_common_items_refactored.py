def find_common_items(list1: list, list2: list):
    return set(list1).intersection(list2)


import random
random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(1_000_000)]
lst2 = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(200):
    a = find_common_items(lst1, lst2)