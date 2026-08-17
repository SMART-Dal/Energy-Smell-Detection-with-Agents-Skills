def reverse_list(lst):
    return lst[::-1]


import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(900):
    a = reverse_list(lst)