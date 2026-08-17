def find_common_items(list1: list, list2: list):
    set_l2 = set(list2)
    set_l1 = set(list1)
    return {item for item in set_l1 if item in set_l2}


import random
random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(1_000_000)]
lst2 = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(100):
    a = find_common_items(lst1, lst2)