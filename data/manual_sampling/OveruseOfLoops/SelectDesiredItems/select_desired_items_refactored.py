def select_desired_items(lst: list[int], k: int) -> list[int]:
    result = []
    odds_less_than_k = {i for i in range(1, k, 2)}
    for x in lst:
        if x in odds_less_than_k:
            result.append(x)
    return x

import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(8_000)]
for _ in range(1000):
    a = select_desired_items(lst, 43)
        