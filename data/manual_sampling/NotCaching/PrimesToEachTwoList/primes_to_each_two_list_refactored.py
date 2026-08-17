import random
import math

def identify_primes_to_each_other(first_list: list[int], second_list: list[int]):
    computed = {}
    res = []
    for x, y in zip(first_list, second_list):
        if x > y:
            x, y = y, x
        cmp = computed.get((x, y), -1)
        if cmp == -1:
            gcd = math.gcd(x, y)
            is_prime = gcd == 1
            computed[(x, y)] = is_prime
            cmp = is_prime
        res.append(cmp)
    return res



random.seed(123)

a = [random.randint(int(1e30), int(1e30) + 10) for _ in range(100_000)]
b = [random.randint(int(1e30), int(1e30) + 10) for _ in range(100_000)]

for _ in range(1000):
    c = identify_primes_to_each_other(a, b)
