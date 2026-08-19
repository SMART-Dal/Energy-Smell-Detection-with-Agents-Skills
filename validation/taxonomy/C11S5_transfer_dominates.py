"""C11.S5 Missed Parallelism -- the repair that is a regression.

The card's own counter-example, from this project's sample set: a matrix
multiply parallelised per row with the whole right-hand matrix sent to every
task. Every argument and every result is pickled both ways, so a task that
receives a large structure and computes briefly is dominated by transfer.

This is the adversarial file for C11.S5 and it exists to be a loss. The card
says two questions prevent the mistake -- is this CPU-bound or I/O-bound, and
how many bytes move per unit of work -- and this puts a number on the second.
"""

from concurrent.futures import ProcessPoolExecutor

WORKERS = 4


def _row_times_matrix(args):
    row, matrix = args
    width = len(matrix[0])
    out = [0] * width
    for k, value in enumerate(row):
        column = matrix[k]
        for j in range(width):
            out[j] += value * column[j]
    return out


def before(a, b):
    return [_row_times_matrix((row, b)) for row in a]


def after(a, b):
    with ProcessPoolExecutor(WORKERS) as pool:
        return list(pool.map(_row_times_matrix, [(row, b) for row in a]))


def _matrix(n, m):
    return [[(i * m + j) % 17 for j in range(m)] for i in range(n)]


def cases():
    return [("big-payload",   lambda: (_matrix(24, 200), _matrix(200, 200))),
            ("small-payload", lambda: (_matrix(24, 20), _matrix(20, 20))),
            ("edge",          lambda: (_matrix(1, 4), _matrix(4, 4)))]
