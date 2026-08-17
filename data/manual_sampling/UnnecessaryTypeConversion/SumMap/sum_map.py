import random

def sum_map(lst: list[int]):
    return sum(list(map(lambda x: 2*x, lst)))

random.seed(1234)
a = [random.randint(0, 100) for _ in range(100_000)]


for _ in range(1000):
    c = sum_map(a)
