def filter_map(lst: list):
    return sum([x for x in map(lambda x: x * 2, lst) if x % 3 == 0])


import random
random.seed(123)
lst = [random.randint(0, 100) for i in range(int(1e5))]
for _ in range(1000):
    a = filter_map(lst)