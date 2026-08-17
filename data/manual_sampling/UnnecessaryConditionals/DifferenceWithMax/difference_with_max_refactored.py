def difference_with_max(lst1: list[int], lst2: list[int]):
    l = []
    for i, j in zip(lst1, lst2):
        l.append(max(i, j))
    
    new_lst1 = []
    new_lst2 = []
    for i, k in enumerate(l):
        new_lst1.append(k - lst1[i])
        new_lst2.append(k - lst2[i])
    
    return new_lst1, new_lst2


import random
random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(100_000)]
lst2 = [random.randint(0, 100) for i in range(100_000)]
for _ in range(650):
    difference_with_max(lst1, lst2)
