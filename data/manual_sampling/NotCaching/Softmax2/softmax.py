import math
import random


def softmax_calc(l: list):
    exp_list = list(map(lambda x: math.exp(x), l))
    return [x / sum(exp_list) for x in exp_list]


random.seed(1234)

for _ in range(2):
    a = softmax_calc([random.randint(int(1e1), int(1e2)) for _ in range(int(4e4))])
