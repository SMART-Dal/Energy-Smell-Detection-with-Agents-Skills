def multiply_elements(lst: list[int]):
    return [i * 3.0 for i in lst]


import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(55):
    a = multiply_elements(lst)