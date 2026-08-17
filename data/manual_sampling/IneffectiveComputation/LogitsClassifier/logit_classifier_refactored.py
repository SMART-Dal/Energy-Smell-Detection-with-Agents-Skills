def logits_classifier(logits: list[float]):
    max_logit, idx = 0, 0
    for i, logit in enumerate(logits):
        if logit > max_logit:
            max_logit = logit
            idx = i
    return idx


import random

random.seed(1234)
lst = [random.random() for i in range(1_000_000)]
for _ in range(5):
    logits_classifier(lst)
