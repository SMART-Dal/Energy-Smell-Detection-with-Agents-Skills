import math


def is_pair_diff_prime(lst_nums: list[tuple[int, int]]):
    pair_diff = [x - y for x, y in lst_nums]
    results = []
    for i in range(len(pair_diff)):
        tmp_res = []
        for j in range(i + 1, len(pair_diff)):
            tmp_res.append(math.gcd(pair_diff[i], pair_diff[j]))
        results.append(tmp_res)
    return results


nums = []
import random

random.seed(1234)
for _ in range(int(1e4)):
    a = random.randint(0, 100)
    b = random.randint(0, 100)
    nums.append((a, b))

for _ in range(1):
    a = is_pair_diff_prime(nums)
