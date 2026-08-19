"""C3.S4 Inefficient Nested Iteration -- every pair's result is wanted.

The card's first `NOT a smell when` clause: the inner loop is not a search, so
there is nothing a lookup can replace and no loop level to remove. The only
edit available is to hoist the row lookup out of the inner loop, which is C3.S2
-- so a small reading here says the nesting was never the finding.
"""

def before(points):
    n = len(points)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            matrix[i][j] = abs(points[i] - points[j])
    return sum(sum(row) for row in matrix)


def after(points):
    n = len(points)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        left = points[i]
        row = matrix[i]
        for j in range(n):
            row[j] = abs(left - points[j])
    return sum(sum(r) for r in matrix)


def cases():
    return [("large",  lambda: (list(range(900)),)),
            ("normal", lambda: (list(range(90)),)),
            ("edge",   lambda: ([1],))]
