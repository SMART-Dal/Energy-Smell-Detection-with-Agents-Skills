import random

def difference_between_numbers(l: list):
    tmp = [[0 for j in range(len(l))] for _ in range(len(l))]
    for i in range(len(l)):
        for j in range(i + 1, len(l)):
            diff = abs(l[i] - l[j])
            tmp[i][j] = diff
            tmp[j][i] = diff
    return tmp

random.seed(123)
tmp = [random.randint(0, 100) for i in range(10_000)]
for _ in range(3):
    a = difference_between_numbers(tmp)