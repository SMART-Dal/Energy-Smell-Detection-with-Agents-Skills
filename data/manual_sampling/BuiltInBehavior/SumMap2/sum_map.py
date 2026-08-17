import random

def sum_map(l: list):
    return sum(map(lambda x: x * 2, l))
    
random.seed(42)
l = [random.randint(0, 100) for i in range(int(1e5))]
for i in range(1000):
    a = sum_map(l)
