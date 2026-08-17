import random

def assign_type(num: int):
    types = ("red", "blue", "green", "yellow")
    return types[num % 4] 
    
random.seed(123)
tmp = random.randint(int(1e7), int(1e8))
for _ in range(300_000_000):
    a = assign_type(tmp)