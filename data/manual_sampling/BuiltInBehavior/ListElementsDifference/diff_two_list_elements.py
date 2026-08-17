def diff_two_lists_elements(lst1, lst2):
    return sum([abs(lst1[i] - lst2[i]) for i in range(len(lst1))])



import random
random.seed(123)
lst1 = [random.randint(0, 100) for i in range(int(1e5))]
lst2 = [random.randint(0, 100) for i in range(int(1e5))]
for _ in range(1000):
    a = diff_two_lists_elements(lst1, lst2)