import heapq
def build_sorted_list_based_on_occurrence(occurrence: dict):
    h = []
    for item, count in occurrence.items():
        heapq.heappush(h, (item, count))
    result = []
    while h:
        item, count = heapq.heappop(h)
        result.extend([item] * count)
    return result

import random
random.seed(1234)
lst = {random.randint(0, 1_000_000): random.randint(0, 100) for i in range(200_000)}
for _ in range(4):
    a = build_sorted_list_based_on_occurrence(lst)