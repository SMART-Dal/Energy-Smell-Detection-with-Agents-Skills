def item_counts(l: list):
    count = {}
    for x in l:
        item_count = count.get(x, -1)
        count[x] = item_count + 1 if item_count != -1 else 1
    return count


import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(30):
    a = item_counts(lst)