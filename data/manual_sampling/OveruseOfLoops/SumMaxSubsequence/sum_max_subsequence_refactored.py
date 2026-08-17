def sum_max_subsequence(lst: list):
    curr_max = float("-inf")
    curr_sum = 0
    for x in lst:
        curr_sum += x
        if curr_sum > curr_max:
            curr_max = curr_sum
        if curr_sum < 0:
            curr_sum = 0
    return curr_max


import random
random.seed(1234)
lst = [random.randint(-100, 100) for i in range(1_000_000)]
for _ in range(10):
    a = sum_max_subsequence(lst)
