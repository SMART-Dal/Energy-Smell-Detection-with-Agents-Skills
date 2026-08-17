def retrieve_bidirectional_edges(edges_list: list[tuple[int, int]], n: int):
    results = []
    adj_matrix = [set() for _ in range(n)]
    for x, y in edges_list:
        adj_matrix[x].add(y)
        if x in adj_matrix[y]:
            results.append({x, y})
    return results

import random
random.seed(1234)
lst = [(random.randint(0, 1000 - 1), random.randint(0, 1000 - 1)) for i in range(1_000_000)]
for _ in range(3):
    a = retrieve_bidirectional_edges(lst, 1000)