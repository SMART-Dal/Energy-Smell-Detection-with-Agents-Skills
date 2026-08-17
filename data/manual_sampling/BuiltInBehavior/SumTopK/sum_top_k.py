def sum_top_k(lst: list, k: int) -> list:
    return sum(sorted(lst)[:k])


import random
random.seed(1234)
lst = [random.randint(0, 10000) for i in range(int(1e6))]
for _ in range(6):
    a = sum_top_k(lst, 100)
