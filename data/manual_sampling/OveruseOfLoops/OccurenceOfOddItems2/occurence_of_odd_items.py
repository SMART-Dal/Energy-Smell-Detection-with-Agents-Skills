def occurence_of_odd_items(lst: list):
    counter = {k: 1 for k in lst if k % 2 == 1}
    for x in lst:
        if x % 2 == 0:
            continue
        counter[x] += 1
    return counter


lst = [i for i in range(0, 200, 2)] * 6000
lst += [1, 3, 3, 5, 7, 1, 3, 9, 3]
import random

random.seed(1234)
for _ in range(50):
    a = occurence_of_odd_items(lst)
