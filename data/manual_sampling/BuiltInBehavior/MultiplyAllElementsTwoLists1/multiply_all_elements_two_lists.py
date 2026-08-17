def multiply_all_elements_two_lists(lst1, lst2):
    res = []
    for x in lst1:
        curr = []
        for y in lst2:
            curr.append(x*y)
        res.append(curr)
    return res


import random
random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(8_000)]
lst2 = [random.randint(0, 100) for i in range(8_000)]
for _ in range(2):
    a = multiply_all_elements_two_lists(lst1, lst2)