def sum_dict_key_values1(d: dict):
    return sum([k + d[k] for k in d])


import random
random.seed(1234)
lst = {i: random.randint(0, 100) for i in range(1000)}
for _ in range(100_000):
    a = sum_dict_key_values1(lst)