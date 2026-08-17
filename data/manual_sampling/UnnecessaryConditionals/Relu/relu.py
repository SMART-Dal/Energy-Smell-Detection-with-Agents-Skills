import random

def relu(x: int):
    if x < 0:
        return 0
    elif x >= 0:
        return x

random.seed(123)
tmp = random.randint(-1_000_000, 1_000_000)
for _ in range(80_000_000):
    a = relu(tmp)
