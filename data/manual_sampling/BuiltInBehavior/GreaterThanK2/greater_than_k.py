def greater_than_k(lst: list, k: int) -> list:
    return {x for x in lst if x > k}



import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(200):
    a = greater_than_k(lst, 50)
