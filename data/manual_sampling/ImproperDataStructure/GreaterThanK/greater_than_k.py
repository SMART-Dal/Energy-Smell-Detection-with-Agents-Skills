def greater_than_k(lst: list, k: int):
    res = []
    for x in lst:
        if x > k and x not in res:
            res.append(x)
    return res



import random
random.seed(1234)
lst = [random.randint(0, 500) for i in range(1_000_000)]
for _ in range(15):
    a = greater_than_k(lst, 50)
