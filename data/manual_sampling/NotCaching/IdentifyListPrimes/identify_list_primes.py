import random

def is_prime(num: int) -> bool:
    if num < 2:
        return False
    for i in range(2, num):
        if num % i == 0:
            return False
    return True

def identify_list_primes(l: list[int]):
    return [is_prime(x) for x in l]

random.seed(123)
tmp = [random.randint(0, 500) for i in range(1_000_000)]
for _ in range(3):
    a = identify_list_primes(tmp)

