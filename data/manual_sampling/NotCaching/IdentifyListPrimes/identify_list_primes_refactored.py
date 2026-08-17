import random

def is_prime(num: int) -> bool:
    if num < 2:
        return False
    for i in range(2, num):
        if num % i == 0:
            return False
    return True


def identify_list_primes(l: list[int]):
    computed = {}
    res = []
    for x in l:
        cmp = computed.get(x, -1)
        if cmp == -1:
            curr_is_prime = is_prime(x)
            computed[x] = curr_is_prime
            cmp = curr_is_prime
        
        res.append(cmp)
    return res


random.seed(123)
tmp = [random.randint(0, 500) for i in range(1_000_000)]
for _ in range(3):
    a = identify_list_primes(tmp)


