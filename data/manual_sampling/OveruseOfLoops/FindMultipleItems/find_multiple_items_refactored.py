def binary_search(sorted_list, target):
    low = 0
    high = len(sorted_list) - 1

    while low <= high:
        mid = (low + high) // 2
        guess = sorted_list[mid]
        if guess == target:
            return mid
        elif guess < target:
            low = mid + 1
        else:
            high = mid - 1
            
    return -1

def find_multiple_items(lst: list[int], queries: list[int]):
    new_lst = sorted(lst)
    res = []
    for q in queries:
        res.append(binary_search(new_lst, q))
    return res


import random

random.seed(1234)
lst = [random.randint(0, 100_000) for i in range(2000)]
queries = [random.randint(0, 100_000) for i in range(200_000)]
for _ in range(2):
    a = find_multiple_items(lst, queries)