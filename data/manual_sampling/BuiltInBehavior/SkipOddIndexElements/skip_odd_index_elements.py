def skip_odd_indexed_elements(lst):
    return [lst[i] for i in range(0, len(lst), 2)]

import random
random.seed(1234)

lst = [random.randint(0, 100) for _ in range(5*10**6)]
for _ in range(15):
    a = skip_odd_indexed_elements(lst)
