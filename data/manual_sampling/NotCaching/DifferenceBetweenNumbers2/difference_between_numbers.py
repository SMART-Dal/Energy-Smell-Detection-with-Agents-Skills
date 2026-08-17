import random

def difference_between_numbers(l: list):
    tmp = []
    for i in range(len(l)):
        row_tmp = []
        for j in range(len(l)):
            row_tmp.append(abs(l[i] - l[j]))
        tmp.append(row_tmp)
    return tmp

random.seed(123)
tmp = [random.randint(0, 100) for i in range(10_000)]
for _ in range(3):
    a = difference_between_numbers(tmp)