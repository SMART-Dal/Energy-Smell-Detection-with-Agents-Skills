def less_and_greater_than_bound(l: list, lower_bound: int, upper_bound: int):
    assert upper_bound > lower_bound
    less = []
    greater = []
    for x in l:
        if x > upper_bound:
            greater.append(x)
        elif x < lower_bound:
            less.append(x)
    return less, greater


import random
random.seed(1234)
lst = [random.randint(0, 100000) for i in range(9_000_000)]
for _ in range(30):
    a = less_and_greater_than_bound(lst, 20000, 80000)