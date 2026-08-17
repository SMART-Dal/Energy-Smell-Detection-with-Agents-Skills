def find_top_k_greater_than_c(lst: list, k: int, c: int) -> list:
    return [x for x in lst if x > c][:k]


import random

random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(25):
    a = find_top_k_greater_than_c(lst, 10_000, 50)