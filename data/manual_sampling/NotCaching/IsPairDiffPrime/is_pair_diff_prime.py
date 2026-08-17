import math


def is_pair_diff_prime(lst_nums: list[tuple[int, int]]):
    results = []
    for i in range(len(lst_nums)):
        tmp_res = []
        xi, yi = lst_nums[i]
        diff_i = xi - yi
        for j in range(i + 1, len(lst_nums)):
            xj, yj = lst_nums[j]
            diff_j = xj - yj
            tmp_res.append(math.gcd(diff_i, diff_j))
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
