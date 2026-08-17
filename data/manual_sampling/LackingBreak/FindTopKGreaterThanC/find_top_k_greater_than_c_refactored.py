def find_top_k_greater_than_c(lst: list, k: int, c: int) -> list:
    res = []
    for x in lst:
        if x > c:
            res.append(x)
            if len(res) == k:
                break
    return res


import random

random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(25):
    a = find_top_k_greater_than_c(lst, 10_000, 50)