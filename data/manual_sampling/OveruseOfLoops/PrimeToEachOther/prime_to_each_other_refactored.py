import math

def find_prime_to_each_other_less_than_k(k):
    res = {}
    for i in range(2, k):
        for j in range(i+1, k):
            if math.gcd(i, j) == 1:
                res.setdefault(i, []).append(j)
                res.setdefault(j, []).append(i)
    return res



a = find_prime_to_each_other_less_than_k(10_000)
