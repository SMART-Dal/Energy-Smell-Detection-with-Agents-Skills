def find_multiple_items(lst: list[int], queries: list[int]):
    res = []
    for q in queries:
        res.append(q if q in lst else -1)
    return res


import random

random.seed(1234)
lst = [random.randint(0, 100_000) for i in range(2000)]
queries = [random.randint(0, 100_000) for i in range(200_000)]
for _ in range(2):
    a = find_multiple_items(lst, queries)