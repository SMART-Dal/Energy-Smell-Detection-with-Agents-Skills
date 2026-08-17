def greater_than_k(lst: list, k: int) -> list:
    res = set()
    for x in lst:
        if x > k and x not in res:
            res.add(x)
    return res



import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(200):
    a = greater_than_k(lst, 50)
