import random

def assign_type(num: int):
    if num % 4 == 0:
        return "red"
    elif num % 4 == 1:
        return "blue"
    elif num % 4 == 2:
        return "green"
    else:
        return "yellow"
    
random.seed(123)
tmp = random.randint(int(1e7), int(1e8))
for _ in range(300_000_000):
    a = assign_type(tmp)