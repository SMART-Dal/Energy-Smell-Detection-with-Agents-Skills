import random

def create_greater_smaller(first_list: list[int], second_list: list[int]):
    merged = zip(first_list, second_list)
    small = []
    great = []
    for x, y in merged:
        if x < y:
            small.append(x)
            great.append(y)
        else:
            small.append(y)
            great.append(x)

    return small, great


random.seed(1234)
a = [random.randint(0, 100) for _ in range(100_000)]
b = [random.randint(0, 100) for _ in range(100_000)]


for _ in range(1000):
    c = create_greater_smaller(a, b)
