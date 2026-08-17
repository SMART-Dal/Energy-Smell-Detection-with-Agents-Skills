import math

def softmax(x):
    exps = [math.exp(i) for i in x]
    sum_exps = sum(exps)
    return [j / sum_exps for j in exps]

def logits_classifier(logits: list[float]):
    probs = softmax(logits)
    max_prob, idx = 0, 0
    for i, prob in enumerate(probs):
        if prob > max_prob:
            max_prob = prob
            idx = i
    return idx


import random

random.seed(1234)
lst = [random.random() for i in range(1_000_000)]
for _ in range(5):
    logits_classifier(lst)