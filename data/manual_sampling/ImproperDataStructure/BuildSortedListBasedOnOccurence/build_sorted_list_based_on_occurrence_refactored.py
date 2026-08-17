def build_sorted_list_based_on_occurrence(occurrence: dict):
    h = []
    key_val = sorted(occurrence.items(), key=lambda x: x[0])
    for key, value in key_val:
        h.extend([key] * value)
    return h

import random
random.seed(1234)
lst = {random.randint(0, 1_000_000): random.randint(0, 100) for i in range(200_000)}
for _ in range(4):
    a = build_sorted_list_based_on_occurrence(lst)