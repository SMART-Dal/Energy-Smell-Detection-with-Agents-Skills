def change_list_elements_type(lst: list):
    return list(map(float, lst))


import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(80):
    a = change_list_elements_type(lst)