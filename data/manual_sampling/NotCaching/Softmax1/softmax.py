import math
import random


def softmax_calc(l: list):
    denominator = sum(list(map(lambda x: math.exp(x), l)))
    return [math.exp(x) / denominator for x in l]


random.seed(1234)
for _ in range(2):
    a = softmax_calc([random.randint(int(1e1), int(1e2)) for _ in range(int(1e7))])
