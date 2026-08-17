def item_counts_of_even_numbers(l: list):
    count = {}
    for x in l:
        if x % 2 == 1:
            continue
        item_count = count.get(x, -1)
        count[x] = count[x] + 1 if item_count != -1 else 1
    return count


import random
random.seed(1234)
lst = [random.randint(0, 100) for i in range(1_000_000)]
for _ in range(100):
    a = item_counts_of_even_numbers(lst)