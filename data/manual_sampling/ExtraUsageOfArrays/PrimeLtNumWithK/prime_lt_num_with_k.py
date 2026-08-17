import math

def prime_lt_num_with_k(num: int, k: int):
    return sum([math.gcd(i, k) == 1 for i in range(2, num)])

for _ in range(65):
    prime_lt_num_with_k(int(6e5), 150_000)
