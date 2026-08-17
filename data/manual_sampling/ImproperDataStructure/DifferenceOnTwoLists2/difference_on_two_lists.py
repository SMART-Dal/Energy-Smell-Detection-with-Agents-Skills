def difference_between_two_list(lst1, lst2):
    diff = set()
    lst2 = set(lst2)
    for x in lst1:
        if x not in lst2:
            diff.add(x)
    return diff



import random
random.seed(1234)
lst1 = [random.randint(0, 1000) for _ in range(1_000_000)]
lst2 = [random.randint(0, 1000) for _ in range(1_000_000)]
for _ in range(300):
    a = difference_between_two_list(lst1, lst2)