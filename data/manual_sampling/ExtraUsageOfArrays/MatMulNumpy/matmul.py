

def matrix_multiplication(A: list[list], B: list[list]) -> list[list]:
    m = len(A)
    n = len(A[0])
    p = len(B[0])
    C = [[0 for _ in range(p)] for _ in range(m)]
    
    for i in range(m):
        for j in range(p):
            total = 0
            for k in range(n):
                total += A[i][k] * B[k][j]
            C[i][j] = total
    return C


import numpy as np
np.random.seed(42)
a = np.random.rand(150, 300).tolist()
b = np.random.rand(300, 450).tolist()
for i in range(10):
    result = matrix_multiplication(a, b)


