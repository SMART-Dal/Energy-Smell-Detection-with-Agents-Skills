def count_abs_less_than_zero(lst: list[int], k: int):
    if k > 0:
        return len(lst)
    return len([1 for x in lst if abs(x) + k > 0])


import random
random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(100_000)]
for _ in range(450):
    count_abs_less_than_zero(lst1, 120)
