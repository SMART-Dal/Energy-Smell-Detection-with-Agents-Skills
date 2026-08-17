import multiprocessing
from concurrent.futures import ProcessPoolExecutor


def _multiply_row(args):
    row_A, B = args
    B_T = list(zip(*B))
    return [sum(a * b for a, b in zip(row_A, col_B)) for col_B in B_T]

def matmul(A, B, num_workers=None):
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    tasks = [(row, B) for row in A]
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        result_rows = executor.map(_multiply_row, tasks)
        return list(result_rows)
    


import random
m, n, p = 500, 500, 500


A = [[random.random() for _ in range(n)] for _ in range(m)]
B = [[random.random() for _ in range(p)] for _ in range(n)]


if __name__ == "__main__":
    for _ in range(2):
        C = matmul(A, B)

