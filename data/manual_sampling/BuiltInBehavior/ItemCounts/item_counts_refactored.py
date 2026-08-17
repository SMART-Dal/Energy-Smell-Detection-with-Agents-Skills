from collections import Counter

def item_counts(l: list):
    return Counter(l)


import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(30):
    a = item_counts(lst)