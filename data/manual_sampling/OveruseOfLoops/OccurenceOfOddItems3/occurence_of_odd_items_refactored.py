def occurence_of_odd_items(lst: list):
    counter = {}
    for x in lst:
        if x % 2 == 0:
            continue
        item_counts = counter.get(x, -1)
        counter[x] = item_counts + 1 if item_counts != -1 else 1
    return counter



lst = [i for i in range(0, 200, 2)] * 6000
lst += [1,3,3,5,7,1,3,9,3]
import random
random.seed(1234)
for _ in range(150):
    a = occurence_of_odd_items(lst)