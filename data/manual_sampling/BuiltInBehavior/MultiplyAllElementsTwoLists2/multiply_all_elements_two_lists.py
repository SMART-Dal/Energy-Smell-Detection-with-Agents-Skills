def multiply_all_elements_two_lists(lst1, lst2):
    res = [[0 for _ in lst2] for _ in lst1]
    for i in range(len(lst1)):
        for j in range(len(lst2)):
            res[i][j] = lst1[i] * lst2[j]
    return res


import random
random.seed(1234)
lst1 = [random.randint(0, 100) for i in range(8_000)]
lst2 = [random.randint(0, 100) for i in range(8_000)]
for _ in range(2):
    a = multiply_all_elements_two_lists(lst1, lst2)