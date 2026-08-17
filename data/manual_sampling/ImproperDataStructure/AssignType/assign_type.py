import random

def assign_type(num: int):
    types = ["red", "blue", "green"]
    return types[num % 3] 
    
random.seed(123)
tmp = random.randint(int(1e7), int(1e8))
for _ in range(80_000_000):
    a = assign_type(tmp)