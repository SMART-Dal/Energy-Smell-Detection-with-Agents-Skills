import math
import random

def softmax_calc(l: list):
    curr_sum = 0
    result = []
    for x in l:
        exp_x = math.exp(x)
        curr_sum += exp_x
        result.append(exp_x)
    return [x / curr_sum for x in result]

random.seed(1234)
for _ in range(2):
    a = softmax_calc([random.randint(int(1e1), int(1e2)) for _ in range(int(1e4))])
